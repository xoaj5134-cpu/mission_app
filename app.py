import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime  # ✅ 제출 시간 저장용

# 기본 설정
st.set_page_config(
    page_title="미션 쇼핑 앱",
    page_icon="🛒",
    layout="wide",
)

# 제출 내용이 저장될 CSV 파일 이름
SUBMISSION_FILE = Path("submissions.csv")


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


# -----------------------------
# products.csv 불러오기
# -----------------------------
def load_products():
    """products.csv 파일을 불러와서 DataFrame으로 반환합니다."""
    products_path = Path("products.csv")

    if not products_path.exists():
        st.error("'products.csv' 파일을 찾을 수 없습니다. 앱과 같은 폴더에 위치시켜 주세요.")
        return pd.DataFrame()

    # ✅ 인코딩을 여러 가지 시도 (UnicodeDecodeError 방지)
    encodings_to_try = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]
    last_error = None
    df = None

    for enc in encodings_to_try:
        try:
            df = pd.read_csv(products_path, encoding=enc)
            break
        except UnicodeDecodeError as e:
            last_error = e
            continue

    if df is None:
        st.error(
            "🚨 'products.csv' 파일을 읽는 동안 인코딩 오류가 발생했습니다.\n\n"
            "파일을 엑셀이나 메모장에서 'UTF-8' 또는 'CSV UTF-8(쉼표로 분리)' 형식으로 다시 저장한 뒤 "
            "다시 업로드/배포해 주세요."
        )
        if last_error:
            st.caption(f"(마지막 오류: {last_error})")
        return pd.DataFrame()

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
    if "이미지URL" in df.columns:
        rename_map["이미지URL"] = "image_url"

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
# 제출 내용 CSV에 저장하는 함수
# -----------------------------
def save_submission_to_csv(reason: str):
    """학생 제출 내용을 submissions.csv에 한 줄씩 추가 저장합니다."""
    # 장바구니 정보를 문자열로 만들어 저장 (엑셀 한 셀에 들어가도록)
    if st.session_state.cart:
        cart_items_str = " | ".join(
            [f"{item['name']}:{item['price']}" for item in st.session_state.cart]
        )
    else:
        cart_items_str = ""

    total = calc_total()
    remaining = (st.session_state.budget or 0) - total

    new_row = {
        "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "미션이름": st.session_state.mission_name,
        "예산": st.session_state.budget,
        "총사용금액": total,
        "남은예산": remaining,
        "장바구니내역": cart_items_str,
        "구매이유": reason,
    }

    new_df = pd.DataFrame([new_row])

    if SUBMISSION_FILE.exists():
        try:
            # 기존 파일 읽어서 뒤에 이어붙이기
            exist_df = pd.read_csv(SUBMISSION_FILE, encoding="utf-8-sig")
            save_df = pd.concat([exist_df, new_df], ignore_index=True)
        except Exception:
            # 혹시 읽기 오류가 나면 새로 생성
            save_df = new_df
    else:
        save_df = new_df

    # ✅ 엑셀에서 잘 열리도록 utf-8-sig로 저장
    save_df.to_csv(SUBMISSION_FILE, index=False, encoding="utf-8-sig")


# -----------------------------
# 1. 시작화면 (미션/예산 선택)
# -----------------------------
def start_page():
    st.title("🧩 미션 선택하기 (시작화면)")
    st.write("학생이 수행할 **미션**을 선택하고, 그에 따른 **예산**을 정하는 화면입니다.")

    st.markdown("---")

    missions = [
        {"label": "월요일 장보기 - 10,000원", "name": "월요일 장보기", "budget": 10000},
        {"label": "화요일 장보기 - 20,000원", "name": "화요일 장보기", "budget": 20000},
        {"label": "수요일 장보기 - 30,000원", "name": "수요일 장보기", "budget": 30000},
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
        # ✅ CSV 파일에 저장
        save_submission_to_csv(reason)
        st.success("제출이 완료되었습니다! 🎉 (submissions.csv에 저장되었습니다.)")

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
