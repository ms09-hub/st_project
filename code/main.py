
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==================================================
# 1. 기본 설정
# ==================================================
st.set_page_config(
    page_title="한강 수계 수질 데이터 분석",
    page_icon="💧",
    layout="wide"
)

st.title("💧 한강 수계 하천 수질 데이터 분석")

st.markdown(
    "### 한강 수계 하천의 수질 특성으로 용존산소량을 추정할 수 있을까?"
)

st.caption("DATA ANALYSIS · WATER QUALITY · DISSOLVED OXYGEN")

st.write(
    "수온, 총유기탄소량(TOC), 수소 이온 농도(pH), "
    "전기전도도 등의 수질 특성을 분석하여 "
    "용존산소량(DO)과의 관계를 탐색합니다."
)

st.divider()


# ==================================================
# 2. GitHub CSV 데이터 연결
# ==================================================
CSV_URL = "https://raw.githubusercontent.com/ms09-hub/st_project/refs/heads/main/data/%ED%95%9C%EA%B0%95%EC%88%98%EA%B3%84_%EC%A0%84%EC%B2%98%EB%A6%AC%EC%99%84%EB%A3%8C_154%ED%96%8911%EC%97%B4-v3.csv"


@st.cache_data(ttl=600)
def load_data():
    try:
        data = pd.read_csv(CSV_URL, encoding="utf-8-sig")
    except UnicodeDecodeError:
        data = pd.read_csv(CSV_URL, encoding="cp949")

    return data


try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.warning("GitHub CSV 링크와 저장소 상태를 확인해주세요.")
    st.code(str(e))
    st.stop()


if df.empty:
    st.error("데이터가 비어 있습니다.")
    st.stop()


# ==================================================
# 3. 데이터 감식
# ==================================================
st.header("1. 데이터 감식")

st.write(
    "수집한 한강 수계 수질 데이터의 규모, 자료형, "
    "결측값을 확인하여 데이터의 기본적인 특성을 파악합니다."
)

col1, col2, col3 = st.columns(3)

col1.metric("전체 행 수", f"{df.shape[0]:,}행")
col2.metric("전체 열 수", f"{df.shape[1]:,}열")
col3.metric("전체 결측값", f"{df.isnull().sum().sum():,}개")


st.subheader("데이터 미리보기")
st.dataframe(df.head(10), use_container_width=True)


# 자료형, 결측값 확인
info_df = pd.DataFrame({
    "컬럼명": df.columns,
    "자료형": df.dtypes.astype(str).values,
    "결측값 수": df.isnull().sum().values
})

st.subheader("컬럼별 데이터 정보")
st.dataframe(info_df, use_container_width=True)


with st.expander("기초 통계량 확인"):
    st.dataframe(
        df.describe().T,
        use_container_width=True
    )


# ==================================================
# 4. 전처리 과정
# ==================================================
st.header("2. 데이터 전처리")

st.write(
    "수집한 원본 자료 중 한강 수계에 해당하는 데이터를 선별하고, "
    "분석에 필요한 측정값이 누락된 행을 제거하여 분석 데이터를 구성했습니다."
)

preprocess_df = pd.DataFrame({
    "단계": [
        "원본 데이터",
        "한강 수계 데이터 선별",
        "결측값 제거 후 최종 데이터"
    ],
    "행 수": [185, 171, 154],
    "처리 내용": [
        "수집한 전체 측정 자료",
        "한강 수계에 해당하지 않는 자료 제외",
        "결측값이 포함된 행 제거"
    ]
})

st.dataframe(preprocess_df, use_container_width=True)


st.markdown("#### 결측값과 이상치 처리 기준")

st.markdown("""
- **결측값:** 측정값이 비어 있는 행은 분석의 정확성을 위해 제외했다.
- **이상치:** 다른 데이터에 비해 크게 벗어난 값은 이상치 후보로 확인했다.
- **처리 기준:** 이상치 후보라도 실제 환경에서 나타날 수 있는 측정값이므로, 명확한 측정 오류가 확인되지 않은 값은 임의로 삭제하지 않았다.
""")

st.info(
    "결측값 제거로 분석 자료의 완전성을 높였지만, "
    "제외된 데이터의 특성이 전체 수질 특성과 달랐을 경우 "
    "분석 결과에 영향을 줄 가능성이 있다."
)


# ==================================================
# 5. 분석할 컬럼 찾기
# ==================================================
def find_column(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


temp_col = find_column(
    df.columns,
    ["수온(℃)", "수온(°C)", "수온", "Temperature"]
)

do_col = find_column(
    df.columns,
    ["DO(㎎/L)", "DO(mg/L)", "DO(mg/l)", "용존산소량", "DO"]
)

toc_col = find_column(
    df.columns,
    ["TOC(㎎/L)", "TOC(mg/L)", "총유기탄소량", "TOC"]
)

ph_col = find_column(
    df.columns,
    ["수소이온농도", "pH", "PH"]
)

ec_col = find_column(
    df.columns,
    ["전기전도도(μS/㎝)", "전기전도도", "EC"]
)


# 수온과 DO가 없으면 분석 중단
if temp_col is None or do_col is None:
    st.error("수온 또는 DO 컬럼을 찾을 수 없습니다.")

    st.write("현재 데이터 컬럼 목록")
    st.write(list(df.columns))

    st.stop()


# 분석할 변수 구성
analysis_cols = [
    col for col in [temp_col, do_col, toc_col, ph_col, ec_col]
    if col is not None
]

analysis_df = df[analysis_cols].copy()

# 숫자 형태로 변환
for col in analysis_cols:
    analysis_df[col] = pd.to_numeric(
        analysis_df[col],
        errors="coerce"
    )


# ==================================================
# 6. 이상치 후보 분석 (IQR)
# ==================================================
st.header("3. 이상치 후보 확인")

st.write(
    "IQR(사분위 범위) 방법을 사용하여 "
    "각 수질 변수에서 일반적인 데이터 범위를 벗어나는 "
    "이상치 후보를 확인합니다."
)

outlier_results = []

for col in analysis_cols:

    values = analysis_df[col].dropna()

    if len(values) == 0:
        continue

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outlier_count = (
        (values < lower) | (values > upper)
    ).sum()

    outlier_results.append({
        "변수": col,
        "Q1": round(q1, 3),
        "Q3": round(q3, 3),
        "IQR": round(iqr, 3),
        "하한": round(lower, 3),
        "상한": round(upper, 3),
        "이상치 후보 수": int(outlier_count)
    })


if outlier_results:
    st.dataframe(
        pd.DataFrame(outlier_results),
        use_container_width=True
    )

st.caption(
    "IQR 범위를 벗어난 값은 이상치 후보일 뿐, "
    실제 측정 오류라고 단정할 수 없습니다. "
    따라서 본 분석에서는 이상치 후보를 임의로 삭제하지 않았습니다."
)


# ==================================================
# 7. DO 데이터 준비
# ==================================================
plot_df = analysis_df.dropna(subset=[do_col]).copy()

do_values = plot_df[do_col]

if len(do_values) == 0:
    st.error("분석 가능한 DO 데이터가 없습니다.")
    st.stop()


# ==================================================
# 8. 그래프 1 : DO 분포
# ==================================================
st.divider()
st.header("4. 용존산소량(DO)의 분포")

st.write(
    "전체 측정 지점에서 용존산소량이 어떤 범위에 분포하는지 "
    "히스토그램으로 확인합니다."
)

fig1, ax1 = plt.subplots(figsize=(10, 5))

ax1.hist(
    do_values,
    bins=15,
    edgecolor="black",
    alpha=0.8
)

ax1.set_title("한강 수계 용존산소량(DO) 분포")
ax1.set_xlabel("용존산소량 (mg/L)")
ax1.set_ylabel("측정 빈도")
ax1.grid(axis="y", alpha=0.3)

st.pyplot(fig1, use_container_width=True)
plt.close(fig1)


# DO 기초 통계
do_mean = do_values.mean()
do_median = do_values.median()
do_min = do_values.min()
do_max = do_values.max()
do_std = do_values.std()


c1, c2, c3, c4 = st.columns(4)

c1.metric("평균 DO", f"{do_mean:.2f} mg/L")
c2.metric("중앙값 DO", f"{do_median:.2f} mg/L")
c3.metric("최솟값 DO", f"{do_min:.2f} mg/L")
c4.metric("최댓값 DO", f"{do_max:.2f} mg/L")


st.subheader("그래프 해석")

st.write(
    f"전체 측정 자료의 평균 용존산소량은 {do_mean:.2f} mg/L, "
    f"중앙값은 {do_median:.2f} mg/L이다. "
    f"DO는 {do_min:.2f}~{do_max:.2f} mg/L 범위에 분포한다."
)

st.write(
    f"표준편차는 {do_std:.2f} mg/L로 나타났다. "
    "히스토그램을 통해 용존산소량이 특정 범위에 집중되는지, "
    "또는 다양한 값으로 분포하는지 확인할 수 있다."
)


# ==================================================
# 9. 그래프 2 : 수온과 DO 관계
# ==================================================
st.divider()
st.header("5. 수온과 용존산소량의 관계")

st.write(
    "수온과 DO를 산점도로 나타내고, "
    "상관계수와 추세선을 통해 두 변수의 관계를 분석합니다."
)

scatter_df = analysis_df.dropna(
    subset=[temp_col, do_col]
).copy()

x = scatter_df[temp_col]
y = scatter_df[do_col]


fig2, ax2 = plt.subplots(figsize=(10, 5))

ax2.scatter(
    x,
    y,
    alpha=0.7,
    label="측정 데이터"
)

# 선형 추세선
if len(scatter_df) >= 2 and x.nunique() >= 2:

    slope, intercept = np.polyfit(x, y, 1)

    trend_x = np.linspace(x.min(), x.max(), 100)
    trend_y = slope * trend_x + intercept

    ax2.plot(
        trend_x,
        trend_y,
        linestyle="--",
        label="선형 추세선"
    )

    ax2.legend()


ax2.set_title("수온과 용존산소량(DO)의 관계")
ax2.set_xlabel("수온 (℃)")
ax2.set_ylabel("용존산소량 (mg/L)")
ax2.grid(alpha=0.3)

st.pyplot(fig2, use_container_width=True)
plt.close(fig2)


# 상관계수
correlation = x.corr(y)

st.metric(
    "수온과 DO의 상관계수",
    f"{correlation:.3f}"
)


st.subheader("그래프 해석")

if correlation < -0.5:

    st.write(
        f"상관계수는 {correlation:.3f}으로 음의 상관관계가 나타났다. "
        "수온이 높아질수록 용존산소량이 낮아지는 경향이 비교적 뚜렷하다."
    )

elif correlation < -0.1:

    st.write(
        f"상관계수는 {correlation:.3f}으로 약한 음의 상관관계를 보였다. "
        "수온이 높아질수록 DO가 감소하는 경향이 있지만, "
        "다른 수질 요인의 영향도 함께 고려할 필요가 있다."
    )

elif correlation <= 0.1:

    st.write(
        f"상관계수는 {correlation:.3f}으로 뚜렷한 선형 관계가 나타나지 않았다. "
        "수온 외에 다른 환경 요인이 DO 변화와 관련되는지 "
        "추가 분석이 필요하다."
    )

else:

    st.write(
        f"상관계수는 {correlation:.3f}으로 양의 상관관계가 나타났다. "
        "일반적으로 예상되는 수온과 DO의 관계와 다를 수 있으므로 "
        "측정 지점이나 시간, 다른 수질 변수의 영향 등을 살펴볼 필요가 있다."
    )


# ==================================================
# 10. 추가 수질 변수와 DO 관계
# ==================================================
st.divider()
st.header("6. 다른 수질 특성과 DO의 관계")

st.write(
    "수온 외에 TOC, pH, 전기전도도가 "
    "용존산소량과 어떤 관계를 보이는지 비교합니다."
)

other_cols = [
    col for col in [toc_col, ph_col, ec_col]
    if col is not None
]

if other_cols:

    correlation_results = []

    for col in other_cols:

        temp_data = analysis_df[[col, do_col]].dropna()

        if len(temp_data) >= 2:

            corr = temp_data[col].corr(temp_data[do_col])

            correlation_results.append({
                "수질 변수": col,
                "DO와의 상관계수": round(corr, 3),
                "데이터 수": len(temp_data)
            })


    if correlation_results:

        st.subheader("수질 변수별 상관관계 비교")

        corr_df = pd.DataFrame(correlation_results)

        st.dataframe(
            corr_df,
            use_container_width=True
        )

        st.caption(
            "상관계수는 두 변수 사이의 선형 관계를 나타내며 "
            "인과관계를 의미하지 않습니다."
        )


        # 각 변수별 산점도
        for col in other_cols:

            temp_data = analysis_df[[col, do_col]].dropna()

            if len(temp_data) < 2:
                continue

            fig, ax = plt.subplots(figsize=(8, 4))

            ax.scatter(
                temp_data[col],
                temp_data[do_col],
                alpha=0.7
            )

            ax.set_title(f"{col}과 DO의 관계")
            ax.set_xlabel(col)
            ax.set_ylabel("용존산소량 (mg/L)")
            ax.grid(alpha=0.3)

            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

else:

    st.info("추가 수질 변수 데이터를 확인할 수 없습니다.")


# ==================================================
# 11. 종합 결론
# ==================================================
st.divider()
st.header("7. 종합 분석 및 결론")

st.write(
    "한강 수계 수질 데이터를 분석하여 용존산소량의 분포를 확인하고, "
    "수온과 DO 사이의 관계를 상관계수와 산점도로 살펴보았다."
)

st.write(
    f"수온과 DO의 상관계수는 {correlation:.3f}으로 나타났다. "
    "이를 통해 두 변수 사이의 관계를 수치적으로 확인했으며, "
    "TOC, pH, 전기전도도 등 다른 수질 특성도 DO와 관련될 수 있음을 탐색했다."
)

st.write(
    "하지만 상관관계만으로 특정 변수가 DO 변화의 원인이라고 "
    "단정하거나 정확한 DO 값을 예측할 수는 없다. "
    "따라서 이후 여러 수질 변수를 동시에 활용하는 회귀 분석을 실시하고, "
    "실제 측정값과 예측값의 차이를 비교하여 "
    "수질 특성으로 용존산소량을 추정할 수 있는지 확인할 필요가 있다."
)


# ==================================================
# 12. 분석의 한계
# ==================================================
with st.expander("분석의 한계 및 추가 탐구"):

    st.markdown("""
    - 2026년 9월 자료를 중심으로 분석하여 계절별 수질 변화는 충분히 반영하지 못했다.
    - 측정 지점, 측정 시간, 하천 환경에 따라 수질이 달라질 수 있다.
    - 결측값이 포함된 자료를 제외했기 때문에 데이터의 특성이 일부 달라졌을 가능성이 있다.
    - 상관관계만으로 원인과 결과를 판단할 수 없다.
    - 향후 회귀 분석을 통해 여러 수질 변수를 활용한 DO 추정 가능성을 확인할 수 있다.
    """)


# ==================================================
# 13. 마무리
# ==================================================
st.divider()

st.caption(
    "한강 수계 수질 데이터를 바탕으로 "
    "수질 특성과 용존산소량의 관계를 탐색한 데이터 분석 프로젝트"
)
