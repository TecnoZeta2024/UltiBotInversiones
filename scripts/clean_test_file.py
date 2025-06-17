import os

file_path = "tests/integration/api/v1/test_real_trading_flow.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Reemplazar el carácter non-breaking space (U+00A0)
    content = content.replace('\u00a0', ' ')
    
    # Reemplazar caracteres de codificación incorrecta (si persisten)
    content = content.replace('Ã³', 'ó')
    content = content.replace('Ã©', 'é')
    content = content.replace('Ã±', 'ñ')
    content = content.replace('Ã¡', 'á')
    content = content.replace('Ã­', 'í')
    content = content.replace('Ãº', 'ú')
    content = content.replace('Ã¼', 'ü')
    content = content.replace('Ã§', 'ç')
    content = content.replace('Â ', ' ') # Este es el \ua0 que se muestra como Â 

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Archivo {file_path} limpiado y reescrito con éxito.")

except Exception as e:
    print(f"Error al limpiar el archivo: {e}")
