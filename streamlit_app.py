import re

import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def replace_log_base_notation(expr: str) -> str:
    expr = expr.replace("ln(", "log(")
    expr = re.sub(r"log_(\d+)\s*\(\s*([^()]+?)\s*\)", r"log(\2, \1)", expr)
    return expr


def format_log_expression(expr: str, default_base: str) -> str:
    expr = replace_log_base_notation(expr)
    if default_base != "e":
        def _replace(match: re.Match) -> str:
            inner = match.group(1)
            return f"log({inner}, {default_base})"

        expr = re.sub(r"log\(\s*([^,()]+?)\s*\)", _replace, expr)
    return expr


def parse_math_expression(expr: str, default_base: str = "10") -> sp.Expr:
    cleaned = format_log_expression(expr.strip(), default_base)
    return parse_expr(
        cleaned,
        local_dict={"log": sp.log, "e": sp.E, "pi": sp.pi},
        transformations=TRANSFORMATIONS,
        evaluate=True,
    )


def evaluate_expression(expr: str, default_base: str = "10") -> str:
    sym_expr = parse_math_expression(expr, default_base)
    simplified = sp.simplify(sym_expr)
    if simplified.free_symbols:
        return str(simplified)
    return str(simplified.evalf())


def solve_log_equation(equation: str, variable_name: str, default_base: str = "10") -> list[dict]:
    if "=" not in equation:
        raise ValueError("방정식은 '=' 기호를 포함해야 합니다.")

    left, right = equation.split("=", 1)
    lhs = parse_math_expression(left, default_base)
    rhs = parse_math_expression(right, default_base)
    variable = sp.symbols(variable_name)
    solutions = sp.solve(sp.Eq(lhs, rhs), variable, dict=True)
    return solutions


st.set_page_config(page_title="로그 계산기", page_icon="🧮")

st.title("🧮 로그 계산기")
st.write("로그 식 계산 및 로그 방정식 풀이를 쉽고 빠르게 확인해보세요.")

with st.expander("사용 예시", expanded=True):
    st.markdown(
        "- `log_2(8)` : 2를 밑으로 하는 로그\n"
        "- `ln(5)` : 자연 로그\n"
        "- `log(x, 2)` : x의 2진 로그\n"
        "- `log_3(x) = 4` : 로그 방정식"
    )

base_option = st.selectbox("기본 로그 밑 선택", ["common (10)", "natural (e)", "custom"])
custom_base = None
if base_option == "custom":
    custom_base = st.text_input("사용자 정의 밑 입력", value="2")

if base_option == "common (10)":
    log_base = "10"
elif base_option == "natural (e)":
    log_base = "e"
else:
    log_base = custom_base or "10"

st.subheader("로그 식 계산")
expression = st.text_input("계산할 로그 식", value="log_2(8)")
if st.button("계산하기", key="eval"):
    try:
        result = evaluate_expression(expression, log_base)
        st.success(f"결과: {result}")
    except Exception as exc:
        st.error(f"식을 계산할 수 없습니다: {exc}")

st.subheader("로그 방정식 풀기")
equation = st.text_input("풀 방정식", value="log_2(x) = 3")
variable = st.text_input("변수", value="x")
if st.button("풀이하기", key="solve"):
    try:
        solutions = solve_log_equation(equation, variable, log_base)
        if solutions:
            for idx, sol in enumerate(solutions, 1):
                st.write(f"{idx}. {variable} = {sol[sp.symbols(variable)]}")
        else:
            st.info("해가 없습니다 또는 수치적 해가 없습니다.")
    except Exception as exc:
        st.error(f"방정식을 풀 수 없습니다: {exc}")
