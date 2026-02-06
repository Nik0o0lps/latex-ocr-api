import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def clean_latex(latex_code: str) -> str:
    """
    Remove formatações desnecessárias do LaTeX gerado pelo modelo
    
    Args:
        latex_code: Código LaTeX bruto
    
    Returns:
        str: LaTeX limpo
    """
    # Remove markdown code blocks
    latex_code = re.sub(r'^```latex\s*', '', latex_code, flags=re.MULTILINE)
    latex_code = re.sub(r'^```\s*$', '', latex_code, flags=re.MULTILINE)
    latex_code = re.sub(r'^```', '', latex_code)
    
    # Remove dollar signs únicos (inline math)
    latex_code = latex_code.strip('$')
    
    # Remove double dollar signs (display math)
    latex_code = latex_code.strip('$$')
    
    # Remove espaços extras
    latex_code = latex_code.strip()
    
    # Remove múltiplas linhas em branco
    latex_code = re.sub(r'\n\s*\n', '\n', latex_code)
    
    return latex_code


def remove_display_math_delimiters(latex_code: str) -> str:
    """
    Remove delimitadores \\[ \\] para renderização
    (Igual ao seu código Streamlit)
    
    Args:
        latex_code: Código LaTeX
    
    Returns:
        str: LaTeX sem \\[ \\]
    """
    cleaned = latex_code.replace(r"\[", "").replace(r"\]", "")
    return cleaned.strip()


def validate_brackets(latex_code: str) -> Tuple[bool, str]:
    """
    Valida se brackets/parênteses estão balanceados
    
    Args:
        latex_code: Código LaTeX
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Pares de brackets
    pairs = {
        '{': '}',
        '[': ']',
        '(': ')'
    }
    
    stack = []
    
    for i, char in enumerate(latex_code):
        if char in pairs.keys():
            stack.append((char, i))
        elif char in pairs.values():
            if not stack:
                return False, f"Unmatched closing bracket '{char}' at position {i}"
            
            opening, pos = stack.pop()
            if pairs[opening] != char:
                return False, f"Mismatched brackets: '{opening}' at {pos} and '{char}' at {i}"
    
    if stack:
        unclosed = ', '.join([f"'{b}' at position {b}" for b in stack])[1]
        return False, f"Unclosed brackets: {unclosed}"
    
    return True, ""


def validate_latex_commands(latex_code: str) -> Tuple[bool, str]:
    """
    Valida comandos LaTeX comuns (básico)
    
    Args:
        latex_code: Código LaTeX
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Comandos que precisam de argumentos
    commands_with_args = [
        r'\\frac', r'\\sqrt', r'\\sum', r'\\int',
        r'\\left', r'\\right', r'\\over'
    ]
    
    for cmd in commands_with_args:
        # Verifica se comando existe sem argumentos apropriados
        pattern = rf'{cmd}\s*(?![{{(\[])'
        if re.search(pattern, latex_code):
            return False, f"Command '{cmd}' appears to be incomplete"
    
    return True, ""


def validate_latex(latex_code: str, strict: bool = False) -> Tuple[bool, str]:
    """
    Validação completa do LaTeX
    
    Args:
        latex_code: Código LaTeX
        strict: Se True, aplica validações mais rigorosas
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not latex_code or not latex_code.strip():
        return False, "Empty LaTeX code"
    
    # Validar brackets
    is_valid, error_msg = validate_brackets(latex_code)
    if not is_valid:
        logger.warning(f"Bracket validation failed: {error_msg}")
        if strict:
            return False, error_msg
    
    # Validar comandos (apenas em strict mode)
    if strict:
        is_valid, error_msg = validate_latex_commands(latex_code)
        if not is_valid:
            logger.warning(f"Command validation failed: {error_msg}")
            return False, error_msg
    
    return True, ""


def post_process_latex(latex_code: str) -> dict:
    """
    Processa LaTeX e retorna versões limpas
    
    Args:
        latex_code: Código LaTeX bruto do modelo
    
    Returns:
        dict: {
            'original': código original,
            'cleaned': código limpo,
            'rendered': código para renderização (sem \\[ \\]),
            'is_valid': booleano,
            'validation_errors': lista de erros
        }
    """
    validation_errors = []
    
    # Limpar
    cleaned = clean_latex(latex_code)
    
    # Versão para renderização
    rendered = remove_display_math_delimiters(cleaned)
    
    # Validar
    is_valid, error_msg = validate_latex(cleaned, strict=False)
    if not is_valid:
        validation_errors.append(error_msg)
    
    result = {
        'original': latex_code,
        'cleaned': cleaned,
        'rendered': rendered,
        'is_valid': is_valid,
        'validation_errors': validation_errors
    }
    
    logger.debug(f"LaTeX post-processing: {result}")
    
    return result


def fix_common_issues(latex_code: str) -> str:
    """
    Tenta corrigir problemas comuns automaticamente
    
    Args:
        latex_code: Código LaTeX
    
    Returns:
        str: LaTeX corrigido
    """
    # Remove espaços extras dentro de comandos
    latex_code = re.sub(r'\\\s+([a-zA-Z]+)', r'\\\1', latex_code)
    
    # Corrige \left e \right sem par
    left_count = latex_code.count(r'\left')
    right_count = latex_code.count(r'\right')
    
    if left_count > right_count:
        # Adiciona \right. no final
        latex_code += r'\right.' * (left_count - right_count)
    elif right_count > left_count:
        # Adiciona \left. no início
        latex_code = r'\left.' * (right_count - left_count) + latex_code
    
    return latex_code
