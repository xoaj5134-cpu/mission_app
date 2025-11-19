import streamlit as st
import pandas as pd
from pathlib import Path

# 기본 설정
st.set_page_config(
    page_title="미션 쇼핑 앱",
    page_icon="🛒",
    layout="wide",
)


# -----------------------------
# Session State 초기화 함수
# -----------------------------
def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "start"  # start, shop, result

    if "mission_name" not in st.session_state:
        st.session_state.mission_name = None

    if "budget" not in st.session_state:
        st.session_state.budget = None

    if "cart" not in st.session_state:
        st.session_state.cart = []  # [{name, price, image_url}, ...]

    if "reason" not in st.session_state:
        st.session_state.reason = ""


# -----------------------------
# 공통 유틸 함수
# -----------------------------
def go_to(page_name: str):
    st.session_state.page = page_name


def calc_total():
    return sum(item["price"] for item in st.session_state.cart)


def load_products():
    """products.csv 파일을 불러와서 DataFrame으로 반환합니다."""
    products_path = Path("products.csv")

    if not products_path.exists():
        st.error("'products.csv' 파일을 찾을 수 없습니다. 앱과 같은 폴더에 위치시켜 주세요.")
        return pd.DataFrame()

    df = pd.read_csv(products_path)

    # 한글 컬럼명을 사용했을 경우를 대비한 매핑
    rename_map = {}
    if "품명" in df.columns:
        rename_map["품명"] = "name"
    if "가격" in df.columns:
        rename_map["가격"] = "price"
    if "imageurl" in df.columns:
        rename_map["imageurl"] = "image_url"
    if "이미지url" in df.columns:
        rename_map["이미지url"] = "image_url"

    if rename_map:
        df = df.rename(columns=rename_map)

    # 필수 컬럼 확인
    required_cols = ["name", "price"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"'products.csv'에 '{col}' 컬럼이 필요합니다.")
            return pd.DataFrame()

    # 이미지 컬럼이 없으면 빈 값으로 채워진 열 생성
    if "image_url" not in df.columns:
        df["image_url"] = None

    # 가격을 숫자로 정리
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)

    return df


# -----------------------------
# 1. 시작화면 (미션/예산 선택)
# -----------------------------
def start_page():
    st.title("🧩 미션 선택하기 (시작화면)")
    st.write("학생이 수행할 **미션**을 선택하고, 그에 따른 **예산**을 정하는 화면입니다.")

    st.markdown("---")

    missions = [
        {"label": "미션 1 - 10,000원", "name": "미션 1", "budget": 10000},
        {"label": "미션 2 - 20,000원", "name": "미션 2", "budget": 20000},
        {"label": "미션 3 - 30,000원", "name": "미션 3", "budget": 30000},
    ]

    labels = [m["label"] for m in missions]

    selected_label = st.radio("도전할 미션을 선택하세요.", labels)

    st.info("미션을 선택한 뒤 **'미션 선택 완료'** 버튼을 누르면 쇼핑화면으로 이동합니다.")

    if st.button("미션 선택 완료 👉"):
        selected_mission = next(m for m in missions if m["label"] == selected_label)
        st.session_state.mission_name = selected_mission["name"]
        st.session_state.budget = selected_mission["budget"]
        st.session_state.cart = []  # 새 미션에서 장바구니 초기화
        go_to("shop")


# -----------------------------
# 2. 쇼핑화면
# -----------------------------
def shop_page():
    st.title("🛒 쇼핑하기 (쇼핑화면)")
    st.write("여러 가지 물품 중에서 원하는 상품을 **장바구니에 담을 수 있는** 화면입니다.")

    # 미션/예산이 없으면 시작화면으로 보내기
    if st.session_state.budget is None or st.session_state.mission_name is None:
        st.warning("먼저 미션을 선택해 주세요.")
        if st.button("미션 선택 화면으로 이동"):
            go_to("start")
        return

    df = load_products()
    if df.empty:
        return  # 에러 메시지는 load_products에서 이미 출력됨

    # 상단 정보 영역
    total = calc_total()
    remaining = st.session_state.budget - total

    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.metric("선택한 미션", st.session_state.mission_name)
    with info_col2:
        st.metric("전체 예산", f"{st.session_state.budget:,} 원")
    with info_col3:
        st.metric("현재 합계 / 남은 예산", f"{total:,} 원 / {remaining:,} 원")

    if remaining < 0:
        st.error("예산을 초과했습니다! 일부 상품을 빼거나 다른 선택을 해 보세요.")

    st.markdown("---")

    # 레이아웃: 왼쪽 상품 목록, 오른쪽 장바구니
    left_col, right_col = st.columns([2, 1])

    # ----- 상품 목록 -----
    with left_col:
        st.subheader("상품 목록")

        for idx, row in df.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 1])

                # 이미지
                with c1:
                    if pd.notna(row["image_url"]) and row["image_url"]:
                        st.image(row["image_url"])
                    else:
                        st.write("이미지 없음")

                # 상품 정보
                with c2:
                    st.write(f"**{row['name']}**")
                    st.write(f"가격: {row['price']:,} 원")

                # 담기 버튼
                with c3:
                    if st.button("담기", key=f"add_{idx}"):
                        st.session_state.cart.append(
                            {
                                "name": row["name"],
                                "price": int(row["price"]),
                                "image_url": row.get("image_url", None),
                            }
                        )
                        st.success(f"'{row['name']}'(이)가 장바구니에 담겼습니다.", icon="✅")

                st.markdown("---")

    # ----- 장바구니 -----
    with right_col:
        st.subheader("장바구니")

        if not st.session_state.cart:
            st.info("아직 장바구니가 비어 있습니다.")
        else:
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_df_display = cart_df[["name", "price"]].rename(
                columns={"name": "상품명", "price": "가격(원)"}
            )
            st.table(cart_df_display)

            cart_total = calc_total()
            st.write(f"**합계: {cart_total:,} 원**")

        st.markdown("---")
        st.info("모든 물건 선택이 끝나면 **'구매하기'** 버튼을 눌러 결과화면으로 이동하세요.")

        if st.button("구매하기 ✅"):
            go_to("result")


# -----------------------------
# 3. 결과화면
# -----------------------------
def result_page():
    st.title("📦 결과 확인하기 (결과화면)")
    st.write("학생이 구매한 물품을 모아서 보여주고, **구매 이유를 작성해 제출**하는 화면입니다.")

    if not st.session_state.cart:
        st.warning("장바구니에 담긴 물건이 없습니다. 먼저 쇼핑을 해 주세요.")
        if st.button("쇼핑화면으로 이동"):
            go_to("shop")
        return

    # 상단 정보
    total = calc_total()
    remaining = st.session_state.budget - total

    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.metric("선택한 미션", st.session_state.mission_name)
    with info_col2:
        st.metric("총 사용 금액", f"{total:,} 원")
    with info_col3:
        st.metric("남은 예산", f"{remaining:,} 원")

    st.markdown("---")

    # 구매한 물품 목록
    st.subheader("🧺 내가 구매한 물품")

    cart_df = pd.DataFrame(st.session_state.cart)
    cart_df_display = cart_df[["name", "price"]].rename(
        columns={"name": "상품명", "price": "가격(원)"}
    )
    st.table(cart_df_display)

    st.markdown("---")

    # 구매 이유 작성
    st.subheader("✍️ 구매 이유 작성")

    reason = st.text_area(
        "왜 이런 물건들을 선택했는지 이유를 적어 보세요.",
        value=st.session_state.reason,
        height=150,
        placeholder="예) 친구들과 함께 나눠 먹을 수 있어서 선택했어요...",
    )

    if st.button("제출"):
        st.session_state.reason = reason
        st.success("제출이 완료되었습니다! 🎉")

    st.markdown("---")
    st.info("다시 미션을 선택하고 싶다면 아래 버튼을 눌러 시작화면으로 돌아갈 수 있습니다.")

    if st.button("처음으로 돌아가기 🔁"):
        # 전체 상태 초기화 후 시작화면 이동
        st.session_state.page = "start"
        st.session_state.mission_name = None
        st.session_state.budget = None
        st.session_state.cart = []
        st.session_state.reason = ""


# -----------------------------
# 메인 실행 부분
# -----------------------------
def main():
    init_state()

    if st.session_state.page == "start":
        start_page()
    elif st.session_state.page == "shop":
        shop_page()
    elif st.session_state.page == "result":
        result_page()
    else:
        # 혹시 모를 예외 상황
        st.session_state.page = "start"
        start_page()


if __name__ == "__main__":
    main()
