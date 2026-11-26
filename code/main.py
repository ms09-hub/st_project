
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="한강 수계 수질 분석",
    page_icon="🌊",
    layout="wide"
)

CSV_URL = "https://raw.githubusercontent.com/ms09-hub/st_project/refs/heads/main/data/%ED%95%9C%EA%B0%95%EC%88%98%EA%B3%84_%EC%A0%84%EC%B2%98%EB%A6%AC%EC%99%84%EB%A3%8C_154%ED%96%8911%EC%97%B4-v3.csv"

st.title("🌊 한강 수계 하천 수질 데이터 분석")
st.subheader("한강 수계 하천의 수질 특성으로 용존산소량을 추정할 수 있을까?")
st.write(
    "수온, TOC, 수소이온농도, 전기전도도 등의 수질 변수와 "
    "용존산소량(DO)의 관계를 데이터와 그래프로 분석합니다."
)


@st.cache_data(ttl=600)
def load_data():
    for encoding in ["utf-8-sig", "cp949", "utf-8"]:
        try:
            return pd.read_csv(CSV_URL, encoding=encoding)
        except Exception:
            continue
    raise ValueError("CSV 데이터를 불러오지 못했습니다.")


try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.info("GitHub CSV 주소와 저장소 공개 설정을 확인해 주세요.")
    st.stop()


def find_column(keywords):
    for col in df.columns:
        name = str(col).replace(" ", "")
        if all(word in name for word in keywords):
            return col
    return None


temp_col = find_column(["수온"])
do_col = find_column(["DO"]) or find_column(["용존산소"])
toc_col = find_column(["TOC"])
ph_col = find_column(["수소이온농도"]) or find_column(["pH"])
ec_col = find_column(["전기전도도"])

analysis_df = df.copy()

for col in [temp_col, do_col, toc_col, ph_col, ec_col]:
    if col is not None:
        analysis_df[col] = pd.to_numeric(
            analysis_df[col], errors="coerce"
        )


# --------------------------------------------------
# 1. 데이터 개요
# --------------------------------------------------

st.divider()
st.header("1. 데이터 개요")

c1, c2, c3 = st.columns(3)

c1.metric("전체 행 수", f"{df.shape[0]}개")
c2.metric("전체 열 수", f"{df.shape[1]}개")
c3.metric("전체 결측값", f"{df.isna().sum().sum()}개")

st.subheader("데이터 미리보기")
st.dataframe(df.head(10), use_container_width=True)

st.subheader("열별 데이터 정보")

info = pd.DataFrame({
    "자료형": df.dtypes.astype(str),
    "결측값 수": df.isnull().sum(),
    "결측률(%)": (df.isnull().mean() * 100).round(2)
})

st.dataframe(info, use_container_width=True)

with st.expander("수치형 데이터 기초 통계"):
    st.dataframe(
        df.describe().transpose(),
        use_container_width=True
    )


# --------------------------------------------------
# 2. 전처리 과정
# --------------------------------------------------

st.divider()
st.header("2. 데이터 전처리 과정")

preprocess = pd.DataFrame({
    "전처리 단계": [
        "원본 데이터",
        "한강 수계 데이터 선별",
        "결측값 제거 후 최종 데이터"
    ],
    "데이터 수": [185, 171, 154]
})

st.dataframe(
    preprocess,
    use_container_width=True,
    hide_index=True
)

st.markdown("""
- 원본 185개 자료에서 동해로 직접 유입되는 하천 자료 14개를 제외하였다.
- 한강 수계 자료 171개 중 결측값이 포함된 17개 행을 제거하였다.
- 최종 154개 자료를 분석에 활용하였다.
- 현재 앱은 전처리가 완료된 CSV 파일을 불러와 분석한다.
""")


# --------------------------------------------------
# 3. 이상치 후보 분석
# --------------------------------------------------

st.divider()
st.header("3. 이상치 후보 확인")

numeric_cols = analysis_df.select_dtypes(
    include=np.number
).columns

outlier_result = []

for col in numeric_cols:
    values = analysis_df[col].dropna()

    if len(values) < 4:
        continue

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    count = ((values < lower) | (values > upper)).sum()

    outlier_result.append({
        "항목": col,
        "IQR 하한": round(lower, 3),
        "IQR 상한": round(upper, 3),
        "이상치 후보 수": int(count)
    })

if outlier_result:
    st.dataframe(
        pd.DataFrame(outlier_result),
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "IQR 범위를 벗어난 값은 이상치 후보일 뿐, "
    "실제 측정 오류라고 단정할 수 없습니다. "
    "따라서 본 분석에서는 이상치 후보를 임의로 삭제하지 않았습니다."
)


# --------------------------------------------------
# 4. DO 분포
# --------------------------------------------------

st.divider()
st.header("4. 용존산소량(DO) 분포")

if do_col is not None:

    do_values = analysis_df[do_col].dropna()

    if len(do_values) > 0:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("평균", f"{do_values.mean():.2f} mg/L")
        c2.metric("중앙값", f"{do_values.median():.2f} mg/L")
        c3.metric("최솟값", f"{do_values.min():.2f} mg/L")
        c4.metric("최댓값", f"{do_values.max():.2f} mg/L")

        fig, ax = plt.subplots(figsize=(8, 4))

        ax.hist(
            do_values,
            bins=12,
            edgecolor="black"
        )

        ax.set_title("Distribution of Dissolved Oxygen")
        ax.set_xlabel("DO (mg/L)")
        ax.set_ylabel("Frequency")
        ax.grid(axis="y", alpha=0.25)

        st.pyplot(fig)
        plt.close(fig)

        st.write(
            f"DO의 평균은 {do_values.mean():.2f} mg/L, "
            f"중앙값은 {do_values.median():.2f} mg/L이다. "
            "히스토그램을 통해 DO 값이 어느 구간에 집중되어 있는지 "
            "확인할 수 있다."
        )

    else:
        st.warning("DO 데이터가 존재하지 않습니다.")

else:
    st.warning("DO 열을 찾지 못했습니다.")


# --------------------------------------------------
# 5. 수온과 DO의 관계
# --------------------------------------------------

st.divider()
st.header("5. 수온과 용존산소량의 관계")

if temp_col is not None and do_col is not None:

    pair = analysis_df[[temp_col, do_col]].dropna()

    if len(pair) >= 2:

        correlation = pair[temp_col].corr(pair[do_col])

        fig, ax = plt.subplots(figsize=(8, 5))

        ax.scatter(
            pair[temp_col],
            pair[do_col],
            alpha=0.75
        )

        ax.set_title("Water Temperature vs. Dissolved Oxygen")
        ax.set_xlabel("Water Temperature (℃)")
        ax.set_ylabel("DO (mg/L)")
        ax.grid(alpha=0.25)

        if pair[temp_col].nunique() >= 2:

            x = pair[temp_col].to_numpy(dtype=float)
            y = pair[do_col].to_numpy(dtype=float)

            slope, intercept = np.polyfit(x, y, 1)

            x_line = np.linspace(x.min(), x.max(), 100)
            y_line = slope * x_line + intercept

            ax.plot(x_line, y_line)

        st.pyplot(fig)
        plt.close(fig)

        st.metric(
            "수온과 DO의 상관계수",
            f"{correlation:.3f}"
        )

        if correlation < 0:
            st.write(
                f"수온과 DO 사이에 음의 상관관계가 나타났다. "
                f"상관계수는 {correlation:.3f}이며, "
                "이 자료에서는 수온이 높아질수록 DO가 낮아지는 경향을 보인다."
            )

        elif correlation > 0:
            st.write(
                f"수온과 DO 사이에 양의 상관관계가 나타났다. "
                f"상관계수는 {correlation:.3f}이다. "
                "예상과 다른 결과라면 측정 시기와 하천 위치, "
                "다른 수질 요인도 함께 확인할 필요가 있다."
            )

        else:
            st.write(
                "수온과 DO 사이에 선형적인 상관관계가 거의 나타나지 않았다."
            )

        st.caption(
            "상관관계는 두 변수의 관련성을 나타내며, "
            "인과관계를 직접 증명하지는 않는다."
        )

    else:
        st.warning("수온과 DO를 함께 분석할 수 있는 자료가 부족합니다.")

else:
    st.warning("수온 또는 DO 열을 확인할 수 없습니다.")


# --------------------------------------------------
# 6. 다른 수질 변수와 DO 비교
# --------------------------------------------------

st.divider()
st.header("6. 다른 수질 변수와 DO의 관계")

other_variables = [
    ("TOC", toc_col),
    ("수소이온농도(pH)", ph_col),
    ("전기전도도", ec_col)
]

for label, col in other_variables:

    if col is None or do_col is None:
        continue

    pair = analysis_df[[col, do_col]].dropna()

    if len(pair) < 2 or pair[col].nunique() < 2:
        continue

    correlation = pair[col].corr(pair[do_col])

    with st.expander(f"{label}와 DO의 관계"):

        fig, ax = plt.subplots(figsize=(7, 4))

        ax.scatter(
            pair[col],
            pair[do_col],
            alpha=0.7
        )

        ax.set_title(f"{label} vs. DO")
        ax.set_xlabel(str(col))
        ax.set_ylabel("DO (mg/L)")
        ax.grid(alpha=0.25)

        st.pyplot(fig)
        plt.close(fig)

        st.write(
            f"상관계수: {correlation:.3f}"
        )

        st.write(
            "그래프와 상관계수를 함께 살펴 변수와 DO 사이의 "
            "관계를 확인할 수 있다. 단, 상관관계가 인과관계를 의미하지는 않는다."
        )


# --------------------------------------------------
# 7. 결론
# --------------------------------------------------

st.divider()
st.header("7. 분석 결론")

st.markdown("""
이번 분석에서는 한강 수계 하천의 수질 데이터에서
용존산소량(DO)의 분포를 확인하고,
수온 및 다른 수질 변수와의 관계를 그래프로 살펴보았다.

특히 수온과 DO의 산점도 및 상관계수를 통해
두 변수 사이의 관계를 수치적으로 확인할 수 있었다.

그러나 이번 자료는 제한된 측정 시기의 데이터이므로
모든 계절과 하천에 일반화하기 어렵다.
또한 상관관계만으로 DO 변화의 원인을 확정할 수 없다.

앞으로 더 다양한 측정 시기와 지점의 데이터를 확보한다면
수질 특성을 바탕으로 DO를 추정하는 분석의 신뢰도를
높일 수 있을 것이다.
""")

st.caption(
    "※ 본 앱은 탐색적 데이터 분석을 위한 앱이며, "
    "DO 예측 모델을 학습하거나 실제 예측값을 제공하지 않습니다."
)
