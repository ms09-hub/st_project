
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. 기본 설정
# ==========================================
st.set_page_config(
    page_title="한강 수계 수질 데이터 분석",
    page_icon="💧",
    layout="wide"
)

st.title("💧 한강 수계 하천 수질 데이터 분석")

st.markdown(
    "### 한강 수계 하천의 수질 특성으로 용존산소량을 추정할 수 있을까?"
)

st.caption("DATA ANALYSIS | WATER QUALITY | DISSOLVED OXYGEN")

st.write(
    "수온, 총유기탄소량(TOC), 수소 이온 농도(pH), "
    "전기전도도(EC) 등의 수질 특성을 분석하여 "
    "용존산소량(DO)과의 관계를 탐색합니다."
)

st.divider()


# ==========================================
# 2. 구글 스프레드시트 데이터 불러오기
# ==========================================
SHEET_ID = "1xZZcv7xwKxEPU3BdyigqsTK9PVZnCtzh"

# 첫 번째 시트(gid=0)를 CSV 형식으로 불러오기
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid=0"
)


@st.cache_data(ttl=600)
def load_data():
    data = pd.read_csv(CSV_URL)
    return data


try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")

    st.info(
        "Google 스프레드시트의 공유 설정을 확인하세요. "
        "링크가 있는 모든 사용자가 뷰어로 설정되어 있어야 합니다."
    )

    st.stop()


if df.empty:
    st.error("불러온 데이터가 비어 있습니다.")
    st.stop()


# ==========================================
# 3. 데이터 개요
# ==========================================
st.header("1. 데이터 감식")

st.write(
    "수집한 한강 수계 수질 데이터의 전체 규모와 "
    "자료형, 결측값 현황을 확인합니다."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("데이터 행 수", f"{df.shape[0]}행")

with col2:
    st.metric("데이터 열 수", f"{df.shape[1]}열")

with col3:
    st.metric("결측값 수", f"{int(df.isnull().sum().sum())}개")


st.subheader("데이터 미리보기")
st.dataframe(df.head(10), use_container_width=True)


# 자료형 및 결측값 확인
info_df = pd.DataFrame({
    "열 이름": df.columns,
    "자료형": [str(dtype) for dtype in df.dtypes],
    "결측값 수": df.isnull().sum().values
})

st.subheader("자료형 및 결측값 확인")
st.dataframe(info_df, use_container_width=True)


with st.expander("수치형 데이터 기초 통계"):
    st.dataframe(
        df.describe().T,
        use_container_width=True
    )


# ==========================================
# 4. 데이터 전처리 과정
# ==========================================
st.header("2. 데이터 전처리")

st.write(
    "한강 수계에 해당하는 데이터를 선별하고, "
    "결측값이 있는 행을 제외하여 분석에 활용했습니다."
)

preprocess_df = pd.DataFrame({
    "전처리 과정": [
        "원본 데이터",
        "한강 수계 데이터 선별",
        "결측값 제거 후 최종 데이터"
    ],
    "데이터 수": [
        185,
        171,
        154
],
    "처리 내용": [
        "전체 수질 측정 자료",
        "한강 수계와 직접 관련되지 않은 자료 제외",
        "결측값이 포함된 행 제거"
    ]
})

st.dataframe(preprocess_df, use_container_width=True)


st.markdown("#### 결측값과 이상치 처리 기준")

st.write(
    "- **결측값:** 측정값이 비어 있는 행은 분석의 정확성을 위해 제외했습니다."
)

st.write(
    "- **이상치:** 수치가 다른 자료에 비해 크게 벗어나더라도 "
    "측정 오류라고 단정하지 않고 이상치 후보로 확인했습니다."
)

st.write(
    "- **이상치 처리:** 실제 환경의 특성을 반영한 값일 가능성이 있으므로 "
    "일괄 삭제하지 않고 분석에 포함했습니다."
)


# ==========================================
# 5. 분석에 필요한 열 찾기
# ==========================================
def find_column(data, candidates):
    for col in candidates:
        if col in data.columns:
            return col
    return None


temp_col = find_column(
    df,
    ["수온(℃)", "수온(°C)", "수온", "Temperature"]
)

do_col = find_column(
    df,
    ["DO(㎎/L)", "DO(mg/L)", "DO(mg/l)", "용존산소량", "DO"]
)

toc_col = find_column(
    df,
    ["TOC(㎎/L)", "TOC(mg/L)", "총유기탄소량", "TOC"]
)

ph_col = find_column(
    df,
    ["수소이온농도", "pH", "PH"]
)

ec_col = find_column(
    df,
    ["전기전도도(μS/㎝)", "전기전도도", "EC"]
)


# 분석 대상 수치 데이터 정리
required_cols = [do_col, temp_col]

if do_col is None or temp_col is None:
    st.error(
        "수온 또는 DO 열을 찾지 못했습니다. "
        "스프레드시트의 열 이름을 확인해주세요."
    )
    st.write("현재 데이터 열 이름:", list(df.columns))
    st.stop()


analysis_cols = [
    col for col in [temp_col, do_col, toc_col, ph_col, ec_col]
    if col is not None
]

analysis_df = df[analysis_cols].copy()

for col in analysis_cols:
    analysis_df[col] = pd.to_numeric(
        analysis_df[col],
        errors="coerce"
    )


# ==========================================
# 6. 이상치 후보 탐색
# ==========================================
st.subheader("이상치 후보 확인")

outlier_results = []

for col in analysis_cols:

    values = analysis_df[col].dropna()

    if len(values) == 0:
        continue

    Q1 = values.quantile(0.25)
    Q3 = values.quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outlier_count = ((values < lower) | (values > upper)).sum()

    outlier_results.append({
        "변수": col,
        "Q1": round(Q1, 3),
        "Q3": round(Q3, 3),
        "IQR": round(IQR, 3),
        "하한": round(lower, 3),
        "상한": round(upper, 3),
        "이상치 후보 수": int(outlier_count)
    })


if outlier_results:
    outlier_df = pd.DataFrame(outlier_results)
    st.dataframe(outlier_df, use_container_width=True)

    st.caption(
        "IQR 기준을 벗어난 자료는 이상치 후보이며, "
        "실제 측정 오류를 의미하지 않습니다."
    )


# ==========================================
# 7. 그래프 분석에 사용할 데이터
# ==========================================
plot_df = analysis_df.dropna(subset=[do_col]).copy()

do_values = plot_df[do_col]

if len(do_values) == 0:
    st.error("DO 데이터가 없어 그래프를 표시할 수 없습니다.")
    st.stop()


# ==========================================
# 8. 그래프 1 - DO 분포
# ==========================================
st.divider()
st.header("3. 용존산소량(DO)의 분포 분석")

st.write(
    "전체 측정 자료에서 용존산소량이 어떤 범위에 분포하는지 "
    "히스토그램을 통해 확인합니다."
)

fig1, ax1 = plt.subplots(figsize=(9, 5))

ax1.hist(
    do_values,
    bins=15,
    edgecolor="black"
)

ax1.set_title("한강 수계 용존산소량(DO) 분포")
ax1.set_xlabel("용존산소량 (mg/L)")
ax1.set_ylabel("측정 빈도")
ax1.grid(axis="y", alpha=0.3)

st.pyplot(fig1)
plt.close(fig1)


# 통계
do_mean = do_values.mean()
do_median = do_values.median()
do_min = do_values.min()
do_max = do_values.max()
do_std = do_values.std()


col1, col2, col3, col4 = st.columns(4)

col1.metric("평균 DO", f"{do_mean:.2f} mg/L")
col2.metric("중앙값 DO", f"{do_median:.2f} mg/L")
col3.metric("최솟값 DO", f"{do_min:.2f} mg/L")
col4.metric("최댓값 DO", f"{do_max:.2f} mg/L")


st.markdown("#### 그래프 해석")

st.write(
    f"측정된 용존산소량의 평균은 **{do_mean:.2f} mg/L**, "
    f"중앙값은 **{do_median:.2f} mg/L**입니다. "
    f"측정값은 {do_min:.2f}~{do_max:.2f} mg/L 범위에 분포합니다."
)

st.write(
    f"표준편차는 {do_std:.2f} mg/L로, "
    "측정 지점에 따라 용존산소량에 차이가 나타날 수 있음을 보여줍니다. "
    "이 분포를 통해 한강 수계의 DO 측정값이 어느 범위에 집중되는지 "
    "확인할 수 있습니다."
)


# ==========================================
# 9. 그래프 2 - 수온과 DO 관계
# ==========================================
st.divider()
st.header("4. 수온과 용존산소량의 관계")

st.write(
    "수온 변화에 따라 용존산소량이 어떻게 달라지는지 "
    "산점도와 상관계수를 이용하여 분석합니다."
)

scatter_df = analysis_df.dropna(
    subset=[temp_col, do_col]
).copy()

x = scatter_df[temp_col]
y = scatter_df[do_col]


fig2, ax2 = plt.subplots(figsize=(9, 5))

ax2.scatter(
    x,
    y,
    alpha=0.7
)

# 추세선
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

st.pyplot(fig2)
plt.close(fig2)


# 상관계수
correlation = x.corr(y)

st.metric("수온과 DO의 상관계수", f"{correlation:.3f}")


st.markdown("#### 그래프 해석")

if correlation < -0.5:
    st.write(
        f"상관계수는 {correlation:.3f}으로, "
        "수온과 DO 사이에 비교적 뚜렷한 음의 상관관계가 나타납니다. "
        "수온이 높아질수록 DO가 낮아지는 경향을 확인할 수 있습니다."
    )

elif correlation < -0.1:
    st.write(
        f"상관계수는 {correlation:.3f}으로 음의 상관관계를 보입니다. "
        "수온이 높아질수록 DO가 감소하는 경향이 있으나, "
        "그 관계가 강하지 않아 다른 수질 요인도 함께 고려할 필요가 있습니다."
    )

elif correlation <= 0.1:
    st.write(
        f"상관계수는 {correlation:.3f}으로, "
        "수온과 DO 사이의 뚜렷한 선형 관계가 나타나지 않습니다. "
        "수온 외의 요인이 DO에 영향을 미치는지 추가로 확인해야 합니다."
    )

else:
    st.write(
        f"상관계수는 {correlation:.3f}으로 양의 상관관계를 보입니다. "
        "일반적으로 예상되는 수온과 DO의 관계와 다를 수 있으므로 "
        "측정 지점, 측정 시각, 다른 수질 변수 등의 영향을 "
        "추가로 살펴볼 필요가 있습니다."
    )


# ==========================================
# 10. 추가 수질 변수 분석
# ==========================================
st.divider()
st.header("5. 다른 수질 특성과 DO의 관계")

st.write(
    "수온 외에도 TOC, pH, 전기전도도가 DO와 어떤 관계를 보이는지 "
    "상관계수를 통해 비교합니다."
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
                "분석 자료 수": len(temp_data)
            })

    if correlation_results:

        corr_df = pd.DataFrame(correlation_results)

        st.dataframe(
            corr_df,
            use_container_width=True
        )

        st.caption(
            "상관계수는 변수 사이의 선형 관계를 나타내며, "
            "인과관계를 의미하지 않습니다."
        )

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

            ax.set_title(f"{col}과 용존산소량(DO)의 관계")
            ax.set_xlabel(col)
            ax.set_ylabel("용존산소량 (mg/L)")
            ax.grid(alpha=0.3)

            st.pyplot(fig)
            plt.close(fig)

else:
    st.info("추가 수질 변수 데이터를 확인할 수 없습니다.")


# ==========================================
# 11. 종합 결론
# ==========================================
st.divider()
st.header("6. 종합 분석 및 결론")

st.write(
    "이번 분석에서는 한강 수계 수질 데이터를 이용하여 "
    "용존산소량의 분포와 수온을 비롯한 여러 수질 특성과의 관계를 "
    "살펴보았습니다."
)

st.write(
    f"수온과 DO의 상관계수는 {correlation:.3f}으로 나타났으며, "
    "이를 통해 두 변수 사이의 관계를 수치적으로 확인할 수 있었습니다. "
    "또한 TOC, pH, 전기전도도와 DO의 관계를 비교하여 "
    "용존산소량이 여러 환경 요인과 관련될 수 있음을 탐색했습니다."
)

st.write(
    "그러나 상관관계만으로 용존산소량을 정확하게 예측하거나 "
    "특정 수질 요인이 DO 변화의 원인이라고 단정할 수는 없습니다. "
    "따라서 이후에는 여러 수질 변수를 동시에 고려한 회귀 분석을 실시하고, "
    "실제 DO 측정값과 예측값을 비교하여 "
    "수질 특성으로 용존산소량을 추정할 수 있는지 확인할 필요가 있습니다."
)


# ==========================================
# 12. 분석의 한계
# ==========================================
with st.expander("분석의 한계 및 추가 탐구"):

    st.write(
        "- 2026년 9월 데이터 중심으로 분석하여 계절별 차이를 충분히 반영하지 못했습니다."
    )

    st.write(
        "- 측정 지점과 측정 시각에 따라 수질이 달라질 가능성이 있습니다."
    )

    st.write(
        "- 결측값이 포함된 자료를 제외했기 때문에 데이터가 가진 특성이 일부 달라졌을 수 있습니다."
    )

    st.write(
        "- 상관관계 분석만으로 원인과 결과를 판단할 수 없습니다."
    )

    st.write(
        "- 이후 회귀 분석을 통해 수온, TOC, pH, 전기전도도를 이용한 DO 추정 가능성을 확인할 수 있습니다."
    )


st.caption(
    "본 분석은 한강 수계 수질 데이터를 바탕으로 수질 특성과 "
    "용존산소량의 관계를 탐색하기 위한 데이터 분석 프로젝트입니다."
)
