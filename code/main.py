import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="한강 수계 DO 데이터 분석",
    page_icon="💧",
    layout="wide"
)

# ==========================================
# 2. 디자인
# ==========================================
st.title("💧 한강 수계 하천 수질 데이터 분석")
st.markdown("### 한강 수계 하천의 수질 특성으로 용존산소량을 추정할 수 있을까?")
st.caption("DATA ANALYSIS | WATER QUALITY | DISSOLVED OXYGEN")

st.markdown("""
수온, 총유기탄소량(TOC), 수소이온농도(pH), 전기전도도(EC) 등의
수질 특성을 분석하여 용존산소량(DO)과의 관계를 탐색합니다.
""")

st.divider()

# ==========================================
# 3. 데이터 불러오기
# ==========================================
FILE_NAME = "한강수계_전처리완료_154행11열-v3.xlsx"

@st.cache_data
def load_data():
    return pd.read_excel(FILE_NAME)

try:
    df = load_data()
except Exception as e:
    st.error("데이터 파일을 불러오지 못했습니다.")
    st.info("Excel 파일과 main.py가 같은 폴더에 있는지 확인하세요.")
    st.stop()

# ==========================================
# 4. 데이터 기본 정보
# ==========================================
st.header("01. 데이터 감식")

st.markdown("### 데이터 기본 정보")

col1, col2, col3, col4 = st.columns(4)

col1.metric("데이터 행 수", f"{df.shape[0]:,}행")
col2.metric("데이터 열 수", f"{df.shape[1]:,}열")
col3.metric("전체 결측치", f"{df.isnull().sum().sum():,}개")
col4.metric("측정 기간", "2026년 9월")

st.markdown("### 데이터 미리보기")

st.dataframe(
    df.head(10),
    use_container_width=True,
    hide_index=True
)

with st.expander("전체 데이터 확인"):
    st.dataframe(df, use_container_width=True, hide_index=True)

# ==========================================
# 5. 자료형 및 결측치 확인
# ==========================================
st.markdown("### 자료형 및 결측치 확인")

data_info = pd.DataFrame({
    "컬럼명": df.columns,
    "자료형": df.dtypes.astype(str).values,
    "결측치 수": df.isnull().sum().values
})

st.dataframe(
    data_info,
    use_container_width=True,
    hide_index=True
)

st.markdown("### 기초 통계량")

numeric_df = df.select_dtypes(include="number")

st.dataframe(
    numeric_df.describe().round(2),
    use_container_width=True
)

st.divider()

# ==========================================
# 6. 전처리 과정
# ==========================================
st.header("02. 데이터 전처리")

st.markdown("""
행정상 한강 권역에 포함되지만 실제로 동해로 유입되는 하천 데이터를 제외하여
분석 대상의 지리적 범위를 실제 한강 수계로 맞추었습니다.

이후 측정값이 누락된 데이터를 제거하여 분석에 사용할 데이터를 정리했습니다.
""")

col1, col2, col3 = st.columns(3)

col1.metric("원본 데이터", "185행")
col2.metric("한강 수계 필터링", "171행")
col3.metric("결측치 제거 후", f"{df.shape[0]}행")

st.markdown("#### 데이터 처리 단계")

process_df = pd.DataFrame({
    "처리 단계": [
        "원본 데이터 수집",
        "한강 수계 외 데이터 제외",
        "결측치 제거",
        "최종 분석 데이터"
    ],
    "행 수": [
        185,
        171,
        154,
        df.shape[0]
    ],
    "처리 내용": [
        "전체 수질 측정 데이터",
        "실제 한강 수계가 아닌 데이터 14행 제외",
        "측정값이 누락된 데이터 17행 제거",
        "최종 분석에 활용"
    ]
})

st.dataframe(
    process_df,
    use_container_width=True,
    hide_index=True
)

st.markdown("### 결측치와 이상치의 구분")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **결측치**

    측정값이 기록되지 않은 데이터입니다.
    분석 변수의 값이 비어 있는 경우를 의미합니다.
    """)

with col2:
    st.warning("""
    **이상치**

    다른 데이터와 비교했을 때 유독 크거나 작은 값입니다.
    이상치라고 해서 반드시 잘못된 측정값은 아니므로
    확인 없이 삭제하지 않습니다.
    """)

st.markdown("### 이상치 탐색 (IQR 기준)")

st.markdown("""
사분위수 범위(IQR)를 이용하여 수치형 변수의 이상치 후보를 탐색합니다.

IQR은 3사분위수(Q3)와 1사분위수(Q1)의 차이이며,
Q1 - 1.5 × IQR보다 작거나 Q3 + 1.5 × IQR보다 큰 값을
이상치 후보로 구분합니다.

이 기준은 이상치 후보를 찾기 위한 것이며,
실제 측정 오류라고 확정하거나 자동 삭제하지 않습니다.
""")

outlier_results = []

for col in numeric_df.columns:

    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    count = ((df[col] < lower) | (df[col] > upper)).sum()

    outlier_results.append({
        "변수": col,
        "Q1": round(q1, 2),
        "Q3": round(q3, 2),
        "IQR": round(iqr, 2),
        "이상치 기준(하한)": round(lower, 2),
        "이상치 기준(상한)": round(upper, 2),
        "이상치 후보 수": int(count)
    })

outlier_df = pd.DataFrame(outlier_results)

st.dataframe(
    outlier_df,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "※ 이상치 후보는 삭제하지 않고 그대로 유지했습니다. "
    "실제 환경에서 발생한 값일 가능성도 있기 때문입니다."
)

st.divider()

# ==========================================
# 7. 그래프 1 - DO 분포
# ==========================================
st.header("03. 탐색적 데이터 분석")

st.subheader("그래프 1. 용존산소량(DO)의 분포")

do_col = "DO(㎎/L)"

fig1, ax1 = plt.subplots(figsize=(9, 5))

ax1.hist(
    df[do_col].dropna(),
    bins=15,
    edgecolor="black",
    alpha=0.8
)

ax1.set_title("Distribution of Dissolved Oxygen (DO)")
ax1.set_xlabel("Dissolved Oxygen (mg/L)")
ax1.set_ylabel("Frequency")
ax1.grid(axis="y", alpha=0.3)

st.pyplot(fig1)

# DO 통계
do_mean = df[do_col].mean()
do_median = df[do_col].median()
do_min = df[do_col].min()
do_max = df[do_col].max()
do_std = df[do_col].std()

col1, col2, col3, col4 = st.columns(4)

col1.metric("DO 평균", f"{do_mean:.2f} mg/L")
col2.metric("DO 중앙값", f"{do_median:.2f} mg/L")
col3.metric("DO 최솟값", f"{do_min:.2f} mg/L")
col4.metric("DO 최댓값", f"{do_max:.2f} mg/L")

st.markdown("#### 그래프 해석")

st.write(
    f"""
    분석 데이터의 용존산소량 평균은 **{do_mean:.2f} mg/L**,
    중앙값은 **{do_median:.2f} mg/L**이다.
    최솟값은 **{do_min:.2f} mg/L**, 최댓값은 **{do_max:.2f} mg/L**로 나타났다.
    데이터의 표준편차는 **{do_std:.2f} mg/L**이다.

    히스토그램을 통해 DO값이 어느 구간에 집중되어 있는지,
    분포가 한쪽으로 치우쳐 있는지,
상대적으로 크거나 작은 값이 존재하는지 확인할 수 있다.
    """
)

st.divider()

# ==========================================
# 8. 그래프 2 - 수온과 DO의 관계
# ==========================================
st.subheader("그래프 2. 수온과 용존산소량(DO)의 관계")

temp_col = "수온(℃)"

x = df[temp_col]
y = df[do_col]

fig2, ax2 = plt.subplots(figsize=(9, 5))

ax2.scatter(
    x,
    y,
    alpha=0.7
)

# 추세선
slope, intercept = np.polyfit(x, y, 1)

trend_x = np.linspace(x.min(), x.max(), 100)
trend_y = slope * trend_x + intercept

ax2.plot(
    trend_x,
    trend_y,
    linestyle="--",
    linewidth=2,
    label="Linear Trend"
)

ax2.set_title("Water Temperature vs Dissolved Oxygen")
ax2.set_xlabel("Water Temperature (℃)")
ax2.set_ylabel("Dissolved Oxygen (mg/L)")
ax2.legend()
ax2.grid(alpha=0.3)

st.pyplot(fig2)

# 상관계수
correlation = df[temp_col].corr(df[do_col])

st.metric(
    "수온과 DO의 상관계수",
    f"{correlation:.3f}"
)

st.markdown("#### 그래프 해석")

if correlation < -0.5:
    relationship = "뚜렷한 음의 상관관계"
elif correlation < -0.2:
    relationship = "약한 음의 상관관계"
elif correlation <= 0.2:
    relationship = "뚜렷하지 않은 선형 관계"
elif correlation <= 0.5:
    relationship = "약한 양의 상관관계"
else:
    relationship = "뚜렷한 양의 상관관계"

st.write(
    f"""
    수온과 DO의 상관계수는 **{correlation:.3f}**이며,
    이를 기준으로 두 변수 사이에는 **{relationship}**가 나타난다.

    산점도에서 수온이 변할 때 DO가 어떻게 변화하는지 확인할 수 있다.
    화학적으로 물의 온도가 높아지면 기체의 용해도가 감소하는 경향이 있으므로,
    실제 데이터에서도 이러한 경향이 나타나는지 살펴볼 수 있다.

    다만 상관관계가 나타나더라도 수온이 DO 변화의 유일한 원인이라고
    단정할 수는 없다.
    """
)

st.divider()

# ==========================================
# 9. 추가 수질 변수 확인
# ==========================================
st.header("04. 다른 수질 변수 탐색")

st.markdown("""
수온 이외에도 TOC, pH, 전기전도도와 DO 사이의 관계를 살펴봅니다.
이를 통해 용존산소량에 영향을 줄 가능성이 있는 다른 수질 요인을 탐색할 수 있습니다.
""")

other_columns = [
    "TOC(㎎/L)",
    "수소이온농도",
    "전기전도도(μS/㎝)"
]

for col in other_columns:

    corr = df[col].corr(df[do_col])

    st.write(f"**{col} ↔ DO 상관계수: {corr:.3f}**")

    fig, ax = plt.subplots(figsize=(7, 3.5))

    ax.scatter(
        df[col],
        df[do_col],
        alpha=0.6
    )

    ax.set_title(f"{col} vs DO")
    ax.set_xlabel(col)
    ax.set_ylabel("DO (mg/L)")
    ax.grid(alpha=0.3)

    st.pyplot(fig)

st.divider()

# ==========================================
# 10. 데이터 분석의 한계와 편향
# ==========================================
st.header("05. 분석의 한계")

st.markdown("""
### 데이터의 한계

- **측정 기간 제한:** 2026년 9월 자료만 사용했으므로 계절별 수질 변화까지 설명하기 어렵다.
- **데이터 제거에 따른 편향:** 한강 수계 외 데이터와 결측치 데이터를 제거하면서 특정 측정 지점이나 환경 조건이 분석에서 제외되었을 가능성이 있다.
- **변수의 한계:** 수온, TOC, pH, EC만으로 DO 변화의 모든 원인을 설명하기 어렵다.
- **상관관계와 인과관계:** 변수 사이의 상관관계가 나타나더라도 특정 수질 요인이 DO 변화의 직접적인 원인이라고 확정할 수 없다.
- **측정 지점 차이:** 하천마다 유속, 깊이, 주변 환경 등이 달라 같은 수온에서도 DO가 다르게 나타날 수 있다.

### 데이터 삭제가 분석에 미칠 수 있는 영향

결측치가 특정 측정 지점이나 날짜에 집중되어 있었다면,
해당 환경의 데이터가 분석에서 충분히 반영되지 않을 수 있다.
따라서 데이터 삭제 후 분석 결과가 전체 한강 수계의 특성을
완전히 대표한다고 단정하기 어렵다.
""")

st.divider()

# ==========================================
# 11. 최종 정리
# ==========================================
st.header("06. 탐구 정리")

st.markdown("""
이번 분석에서는 한강 수계의 실제 수질 데이터를 활용하여
용존산소량의 분포와 수온을 비롯한 수질 변수들의 관계를 탐색하였다.

DO 분포 그래프를 통해 용존산소량의 전반적인 분포를 확인하고,
수온과 DO 산점도를 통해 화학에서 학습한 기체 용해도와
실제 하천 데이터의 관계를 비교하였다.

이러한 분석을 바탕으로 여러 수질 특성이 용존산소량 추정에
활용될 수 있는지 탐색하고, 실제 환경 데이터 분석의 가능성과 한계를 확인하였다.
""")

st.success("데이터 탐색 및 분석이 완료되었습니다.")

st.caption("20801 고미선 · 20803 심하율 | 한강 수계 수질 데이터 탐구")
