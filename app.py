import streamlit as st
import pandas as pd


# Mock function to simulate loading athlete data
def load_athlete_data():
    conn = st.connection("sql")
    df = conn.query("SELECT * FROM athlete_info_utf8")
    return df


def load_uploaded_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df['Race Number'] = df['Race Number'].astype(int)  # Ensure race numbers are integers
    return df


# 主函数
def main():
    # 设置页面配置
    st.set_page_config(page_title="TRI INFO BY ZealDon-铁人三项检录应用", page_icon="🏆", layout="wide")
    st.title("TRI INFO BY ZealDon-铁人三项检录应用")
    # 添加比赛名称输入框
    competition_name = st.text_input("请输入比赛名称", key="competition_name")
    if competition_name:
        st.subheader(f"比赛名称: {competition_name}")
    # 初始化会话状态变量
    if 'race_number' not in st.session_state:
        st.session_state.race_number = ""
    if 'athlete_info' not in st.session_state:
        st.session_state.athlete_info = None

    # 仅在未上传检录名单时显示上传器
    if 'checkin_df' not in st.session_state:
        uploaded_file = st.file_uploader("请上传检录名单 Excel 文件", type=["xlsx", "xls"],
                                         key="uploader_checkin_global")
        if uploaded_file is not None:
            try:
                st.session_state.checkin_df = load_uploaded_data(uploaded_file)
                st.success("检录名单已上传。")
            except Exception as e:
                st.error(f"上传失败: {e}")
        else:
            st.info("请先上传检录名单 Excel 文件。")
            return  # 上传未完成，结束程序

    # 获取检录名单数据
    checkin_df = st.session_state.checkin_df
    menu = st.sidebar.selectbox("选择功能", ["检录数据匹配", "查询选手"])

    if menu == "检录数据匹配":
        st.header("检录数据匹配")

        # 加载数据库中的运动员数据
        st.write("从数据库加载运动员数据...")
        try:
            athlete_df = load_athlete_data()
            st.write("运动员数据预览:", athlete_df.head())
        except Exception as e:
            st.error(f"无法加载运动员数据: {e}")
            return

        # 进行姓名匹配
        matched_df = pd.merge(checkin_df, athlete_df, left_on='Chinese Name', right_on='Name', how='left')
        st.write("匹配结果:", matched_df)

        # 显示匹配不到的名单
        unmatched = matched_df[matched_df.isnull().any(axis=1)]
        if not unmatched.empty:
            st.warning("以下人员在数据库中未找到匹配：")
            st.write(unmatched)

    elif menu == "查询选手":
        st.header("查询选手信息")
        # 获取所有的 'Race Number' 列表
        race_numbers = checkin_df['Race Number'].unique().tolist()
        race_numbers.sort()
        # 显示当前输入的比赛号码
        st.selectbox("赛手比赛号码:", race_numbers)

        # 定义检录函数
        def lookup_race_number():
            if st.session_state.race_number:
                try:
                    entered_number = int(st.session_state.race_number)
                except ValueError:
                    st.warning("请输入有效的比赛号码。")
                    st.session_state.athlete_info = None
                    st.session_state.race_number = ""
                    return

                # 查找匹配的参赛者
                match = checkin_df[checkin_df['Race Number'] == entered_number]
                if not match.empty:
                    chinese_name = match.iloc[0]['Chinese Name']
                    st.write(f"匹配的选手信息: {chinese_name}")

                    # 加载运动员数据
                    try:
                        athlete_df = load_athlete_data()
                        athlete_info = athlete_df[athlete_df['Name'] == chinese_name]
                        if not athlete_info.empty:
                            st.session_state.athlete_info = athlete_info
                        else:
                            st.session_state.athlete_info = None
                            st.warning("在数据库中未找到该选手的信息。")
                    except Exception as e:
                        st.error(f"无法加载运动员数据: {e}")
                        st.session_state.athlete_info = None
                else:
                    st.session_state.athlete_info = None
                    st.warning("未找到对应的比赛号码")

                # 重置 race_number
                st.session_state.race_number = ""
            else:
                st.warning("请输入比赛号码。")

        # 定义显示选手信息的函数
        def display_athlete_info():
            if st.session_state.athlete_info is not None:
                with st.container():
                    st.subheader("选手信息")
                    st.write(st.session_state.athlete_info)

        # 创建数字键盘布局
        def create_keypad():
            keypad = [
                ['1', '2', '3'],
                ['4', '5', '6'],
                ['7', '8', '9'],
                ['0', '删除', 'Enter']
            ]
            for row in keypad:
                cols = st.columns(3)
                for btn, col in zip(row, cols):
                    if btn == '删除':
                        if col.button(btn, key=btn, use_container_width=True):
                            st.session_state.race_number = st.session_state.race_number[:-1]
                            st.session_state.athlete_info = None
                    elif btn == 'Enter':
                        if col.button(btn, key=btn, use_container_width=True):
                            lookup_race_number()
                    else:
                        if col.button(btn, key=btn, use_container_width=True):
                            st.session_state.race_number += btn
                            # 自动触发检录
                            lookup_race_number()

        # 显示数字键盘
        create_keypad()

        # 显示选手信息
        display_athlete_info()


if __name__ == "__main__":
    main()