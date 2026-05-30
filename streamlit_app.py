import math
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

st.title("🧮 상용로그 계산기")
st.write("밑이 10인 상용로그 값을 계산합니다. 예: `log10(100)` 또는 `log(100)`.")
st.write("상용로그는 숫자를 `N = 10^a × 10^n` 형태로 나타낼 때, `1 <= 10^a < 10`이고 `n`은 정수인 성질을 이용해 계산할 수 있습니다.")

with st.expander("사용 예시", expanded=True):
    st.markdown(
        "- `log10(100)` : 100의 상용로그\n"
        "- `log(1000)` : 1000의 상용로그\n"
        "- `log(5 * 10)` : 곱셈 표현도 계산 가능"
    )

log_base = "10"

def normalize_to_power_of_10(number_text: str) -> tuple[int, float, str]:
    value = float(number_text)
    if value == 0:
        return 0, 0.0, ""

    sign = "" if value >= 0 else "-"
    abs_value = abs(value)
    exponent = math.floor(math.log10(abs_value))
    mantissa = abs_value / (10 ** exponent)
    if mantissa < 1:
        exponent -= 1
        mantissa *= 10
    return exponent, mantissa, sign


def format_scientific(value: float, exponent: int, sign: str) -> str:
    mantissa_text = f"{value:.12g}"
    return f"{sign}{mantissa_text} × 10^{exponent}"


st.subheader("숫자를 10^n × 실수 형태로 변환")
input_number = st.text_input("변환할 숫자 입력", value="768")
if st.button("변환하기", key="normalize"):
    try:
        exponent, mantissa, sign = normalize_to_power_of_10(input_number)
        if exponent == 0 and mantissa == 0.0:
            st.info("입력값이 0입니다. 0은 10^n × a 형태로 표현할 수 없습니다.")
        else:
            st.success(f"변환 결과: {format_scientific(mantissa, exponent, sign)}")
            st.write(f"예: {input_number} = {sign}{mantissa:.12g} × 10^{exponent}")
    except ValueError:
        st.error("유효한 숫자를 입력하세요.")
    except Exception as exc:
        st.error(f"변환 중 오류가 발생했습니다: {exc}")

st.subheader("로그의 성질")
st.write("로그의 기본 성질 중 하나는 `log_a(x) + log_a(y) = log_a(xy)`입니다.")
st.write("상용로그에서는 `log10(x) + log10(y) = log10(xy)`가 성립합니다.")

st.subheader("상용로그 정수/소수 부분 설명")
st.write("상용로그 결과의 정수 부분은 지수의 자리수를 결정합니다. 예를 들어 `log10(768) ≈ 2.885`에서 정수 부분 `2`는 768이 `10^2` 자리에 있다는 뜻입니다.")
st.write("소수 부분은 최고 자리수(가장 큰 자릿값)를 결정합니다. 위 예에서 소수 부분 `0.885`는 768이 `10^2 × 7.68` 형태임을 나타냅니다.")

st.write("예를 들어 `log(245)`는 `2 < log(245) < 3`이고, 정수 부분이 `2`이므로 245는 세 자리수임을 알려줍니다.")
st.write("또한 소수 부분은 `log(2.45)`로 정해지므로 이 값은 `log(2)`와 `log(3)` 사이에 있습니다.")

st.subheader("상용로그 계산")
expression = st.text_input("계산할 로그 식", value="log10(100)")
if st.button("계산하기", key="eval"):
    try:
        result = evaluate_expression(expression, log_base)
        st.success(f"결과: {result}")
    except Exception as exc:
        st.error(f"식을 계산할 수 없습니다: {exc}")

st.subheader("logN = x일 때 N 구하기")
logn_value = st.number_input("log10(N) 값을 입력하세요", value=2.0, step=0.1, format="%.2f")
if st.button("N 계산", key="compute_n"):
    try:
        int_part = math.floor(logn_value)
        frac_part = logn_value - int_part
        mantissa = 10 ** frac_part
        if abs(mantissa - round(mantissa)) < 1e-9:
            mantissa_display = f"{int(round(mantissa))}"
        else:
            mantissa_display = f"{mantissa:.6g}"
        st.success(f"N = 10^{logn_value} = 10^{int_part} × 10^{frac_part:.6f} ≈ 10^{int_part} × {mantissa_display}")
        st.write(f"여기서 `10^{frac_part:.6f}`은 `10^a`이며, `1 <= 10^a < 10`입니다.")
        st.write("정수 부분은 `n`이고 10의 몇 제곱 자리인지 결정하며, 소수 부분은 `a`로서 최고자리수를 결정합니다.")
    except Exception as exc:
        st.error(f"N을 계산할 수 없습니다: {exc}")

st.subheader("밑^지수의 자리수와 최고자리수 계산 (상용로그 사용)")
st.write("상용로그를 사용하면 정수 부분으로 자리수를, 소수 부분으로 최고자리수를 바로 알 수 있습니다.")
base_value = st.number_input("밑 입력", value=2.0, step=1.0, format="%.0f")
exponent_value = st.number_input("지수 입력", value=30.0, step=1.0, format="%.0f")
if st.button("자리수 계산", key="compute_digits"):
    try:
        log10_value = exponent_value * math.log10(base_value)
        int_part = math.floor(log10_value)
        frac_part = log10_value - int_part
        digit_count = int_part + 1
        leading_value = 10 ** frac_part
        leading_digit = int(leading_value)
        upper_bound = leading_digit + 1 if leading_digit < 9 else 10
        lower_log = math.log10(leading_digit)
        upper_log = math.log10(upper_bound)
        st.success(f"{int(base_value)}^{int(exponent_value)}의 자리수는 {digit_count}입니다.")
        st.write(f"log10({int(base_value)}^{int(exponent_value)}) = {log10_value:.6f}")
        st.write(f"정수 부분 {int_part}은 이 수가 10^{int_part}과 10^{int_part + 1} 사이에 있음을 뜻합니다.")
        st.write(f"소수 부분 {frac_part:.6f}은 `10^{{소수 부분}} ≈ {leading_value:.6g}`이어서 최고자리수가 결정됩니다.")
        st.write(f"이 값은 log10({leading_digit}) = {lower_log:.6f}와 log10({upper_bound}) = {upper_log:.6f} 사이에 있으므로 최고자리수는 {leading_digit}입니다.")
        st.write(f"따라서 {int(base_value)}^{int(exponent_value)}의 최고자리수는 {leading_digit}입니다.")
    except Exception as exc:
        st.error(f"자리수를 계산할 수 없습니다: {exc}")
