#!/usr/bin/env python3
"""
SRST (Sistema de Resolución Segmentada de Tests) - Script de Triage Automático
Clasifica automáticamente errores de tests y genera tickets atómicos.
"""

import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum

class ErrorCategory(Enum):
    """Categorías de errores del SRST."""
    DEPRECATION_WARNINGS = "0_DEPRECATION_WARNINGS"
    IMPORT_ERRORS = "1_IMPORT_ERRORS"
    TYPE_ERRORS = "2_TYPE_ERRORS"
    ASYNC_ERRORS = "3_ASYNC_ERRORS"
    DATABASE_ERRORS = "4_DATABASE_ERRORS"
    UI_ERRORS = "5_UI_ERRORS"
    INTEGRATION_ERRORS = "6_INTEGRATION_ERRORS"
    BUSINESS_LOGIC_ERRORS = "7_BUSINESS_LOGIC_ERRORS"
    VALIDATION_ERRORS = "8_VALIDATION_ERRORS"

class ErrorPriority(Enum):
    """Prioridades de errores."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class ErrorTicket:
    """Ticket individual de error SRST."""
    id: str
    category: ErrorCategory
    priority: ErrorPriority
    error_type: str
    file_path: str
    line_number: int
    error_message: str
    test_scope: str
    module: str
    dependencies: List[str]
    estimated_time: int

class SRSTTriage:
    """Clasificador automático de errores para SRST."""
    
    def __init__(self):
        self.base_path = Path.cwd()
        self.tickets: List[ErrorTicket] = []
        self.ticket_counter = 1
        self.resolved_scopes: Set[str] = set()
        
        self.error_patterns: Dict[ErrorCategory, List[str]] = {
            ErrorCategory.DEPRECATION_WARNINGS: [r"PydanticDeprecatedSince20", r"PendingDeprecationWarning"],
            ErrorCategory.IMPORT_ERRORS: [r"ModuleNotFoundError", r"ImportError", r"cannot import name"],
            ErrorCategory.TYPE_ERRORS: [r"TypeError", r"AttributeError"],
            ErrorCategory.ASYNC_ERRORS: [r"Event loop", r"RuntimeError.*asyncio"],
            ErrorCategory.DATABASE_ERRORS: [r"psycopg", r"PoolTimeout", r"sqlalchemy"],
            ErrorCategory.UI_ERRORS: [r"PyQt[56]", r"widget"],
            ErrorCategory.VALIDATION_ERRORS: [r"ValidationError"],
        }
        
        self.critical_modules: List[str] = [
            "src/ultibot_backend/core/",
            "src/ultibot_backend/services/",
            "conftest.py",
            "src/ultibot_backend/main.py",
            "src/ultibot_backend/dependencies.py"
        ]

    def _recreate_ticket_directory(self):
        """Limpia el directorio de tickets para una nueva generación."""
        print("🧹 Limpiando directorio de tickets anterior...")
        tickets_dir = self.base_path / "SRST_TICKETS"
        if tickets_dir.exists():
            shutil.rmtree(tickets_dir)
        tickets_dir.mkdir()
        print("✅ Directorio de tickets listo.")

    def _remove_ansi_codes(self, text: str) -> str:
        """Elimina los códigos de color ANSI del texto."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def run_pytest_collect(self) -> str:
        """
        Ejecuta pytest para recolectar errores y captura la salida en tiempo real.
        """
        print("🚀 Ejecutando 'poetry run pytest --collect-only -q' para obtener datos frescos...")
        command = ["poetry", "run", "pytest", "--collect-only", "-q"]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=False,
                timeout=300  # 5 minutos de timeout
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode != 0 and not output.strip():
                print(f"⚠️  El comando pytest falló con código {result.returncode} pero no produjo salida.")
                return ""

            print("✅ Salida de pytest capturada exitosamente.")
            return self._remove_ansi_codes(output)

        except FileNotFoundError:
            print("❌ Error: 'poetry' no se encontró. Asegúrate de que poetry esté instalado y en el PATH.")
            return ""
        except subprocess.TimeoutExpired:
            print("❌ Error: La ejecución de pytest excedió el tiempo límite de 5 minutos.")
            return ""
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado al ejecutar pytest: {e}")
            return ""

    def classify_error(self, error_type: str) -> Tuple[ErrorCategory, str]:
        """Clasifica un error en una categoría SRST."""
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_type, re.IGNORECASE):
                    return category, pattern
        return ErrorCategory.BUSINESS_LOGIC_ERRORS, "unknown"

    def determine_priority(self, file_path: str, category: ErrorCategory) -> ErrorPriority:
        """Determina la prioridad del error."""
        if any(critical_module in file_path for critical_module in self.critical_modules):
            return ErrorPriority.CRITICAL
        if category in [ErrorCategory.IMPORT_ERRORS, ErrorCategory.DATABASE_ERRORS, ErrorCategory.ASYNC_ERRORS]:
            return ErrorPriority.CRITICAL
        if category == ErrorCategory.VALIDATION_ERRORS:
            return ErrorPriority.HIGH
        if category == ErrorCategory.TYPE_ERRORS:
            return ErrorPriority.HIGH
        return ErrorPriority.MEDIUM

    def extract_module_name(self, file_path: str) -> str:
        """Extrae el nombre del módulo del archivo."""
        path = Path(file_path)
        if "tests/unit" in path.parts:
            try:
                return path.parts[path.parts.index("unit") + 1]
            except IndexError:
                return "unit_test"
        if "tests/integration" in path.parts:
            return "integration_test"
        if "src/ultibot_backend" in path.parts:
            try:
                return path.parts[path.parts.index("ultibot_backend") + 1]
            except IndexError:
                return "backend_core"
        return "unknown"

    def parse_pytest_output(self, output: str) -> List[ErrorTicket]:
        """Parsea la salida de pytest para extraer errores desde el resumen y los bloques de error."""
        tickets: List[ErrorTicket] = []
        processed_scopes: Set[str] = set()

        summary_match = re.search(r'short test summary info\s=+(.*)', output, re.DOTALL)
        if not summary_match:
            return tickets

        summary_content = summary_match.group(1)
        error_lines = re.findall(r'^(ERROR\s.*)$', summary_content, re.MULTILINE)
        
        for line in error_lines:
            parts = line.split(' - ', 1)
            scope = parts[0].replace('ERROR ', '').strip()
            error_message = parts[1] if len(parts) > 1 else "Error durante la recolección de tests."
            
            if scope in processed_scopes:
                continue
            processed_scopes.add(scope)

            error_block_match = re.search(
                rf'_{5,}\sERROR collecting\s{re.escape(scope)}\s_{5,}(.*?)(?=\n_{5,}|\Z)',
                output,
                re.DOTALL
            )
            
            file_path = scope
            line_number = 0
            error_type = error_message.split(':')[0]

            if error_block_match:
                block_content = error_block_match.group(1)
                traceback_match = re.search(r'([^\s>]+?\.py):(\d+):', block_content)
                if traceback_match:
                    file_path = traceback_match.group(1)
                    line_number = int(traceback_match.group(2))
                
                e_line_match = re.search(r'\nE\s+(.*?)$', block_content, re.MULTILINE)
                if e_line_match:
                    error_message = e_line_match.group(1).strip()
                    error_type = error_message.split(':')[0]

            category, _ = self.classify_error(error_type)
            priority = self.determine_priority(file_path, category)
            module = self.extract_module_name(file_path)

            ticket = ErrorTicket(
                id=f"SRST-TEMP-{len(tickets)}",
                category=category,
                priority=priority,
                error_type=error_type,
                file_path=file_path,
                line_number=line_number,
                error_message=error_message,
                test_scope=scope,
                module=module,
                dependencies=[],
                estimated_time=20
            )
            tickets.append(ticket)
        
        return tickets

    def generate_ticket_file(self, ticket: ErrorTicket) -> None:
        """Genera archivo markdown del ticket."""
        ticket_dir = self.base_path / "SRST_TICKETS" / ticket.id
        ticket_dir.mkdir(parents=True, exist_ok=True)
        
        ticket_content = f"""# {ticket.id}: {ticket.error_type} en {ticket.module}

## Error Específico
**Tipo:** `{ticket.error_type}`
**Archivo:** `{ticket.file_path}:{ticket.line_number}`
**Mensaje:** `{ticket.error_message}`
**Categoría:** `{ticket.category.value}`
**Prioridad:** `{ticket.priority.value}`

## Contexto Mínimo
- **Test Scope:** `{ticket.test_scope}`
- **Archivo a tocar:** `{ticket.file_path}`

## Plan de Fix Sugerido
1. [ ] **Analizar:** Revisar el código en `{ticket.file_path}` en la línea {ticket.line_number}.
2. [ ] **Contextualizar:** Entender por qué el test `{ticket.test_scope}` causa este error.
3. [ ] **Refactorizar:** Aplicar la corrección necesaria.
4. [ ] **Validar:** Ejecutar `poetry run pytest {ticket.test_scope}` para confirmar que el error ha desaparecido.

## Validación Inmediata
```bash
# Validar que el error específico desapareció
poetry run pytest -k "{ticket.test_scope}" -v
```

## Criterio de Éxito
- [ ] El error específico ya no aparece en la salida de pytest.
- [ ] La funcionalidad del código modificado sigue siendo la misma.
- [ ] No se han introducido nuevos errores.

**Estado:** `[ ] TODO`
**Tiempo estimado:** `{ticket.estimated_time} minutos`
"""
        (ticket_dir / "description.md").write_text(ticket_content, encoding='utf-8')
        (ticket_dir / "status.md").write_text("TODO", encoding='utf-8')

    def generate_progress_tracker(self) -> None:
        """
        Genera o actualiza el archivo SRST_PROGRESS.md combinando los tickets
        resueltos existentes con los nuevos tickets generados.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        progress_file = self.base_path / "SRST_PROGRESS.md"

        # 1. Generar líneas de texto para los nuevos tickets
        new_ticket_lines = []
        for ticket in self.tickets:
            formatted_line = (
                f"- [ ] **{ticket.id}:** {ticket.error_type} en `{ticket.file_path}` "
                f"(Test: {ticket.test_scope}) - ⏱️ {ticket.estimated_time}min "
                f"[P:{ticket.priority.value}]"
            )
            new_ticket_lines.append(formatted_line)

        # 2. Combinar con las líneas de tickets previamente resueltos
        all_lines = new_ticket_lines + self.resolved_lines

        # 3. Clasificar todas las líneas por prioridad
        critical_lines = sorted([line for line in all_lines if "[P:CRITICAL]" in line])
        high_lines = sorted([line for line in all_lines if "[P:HIGH]" in line])
        medium_lines = sorted([line for line in all_lines if "[P:MEDIUM]" in line])
        low_lines = sorted([line for line in all_lines if "[P:LOW]" in line])
        
        # 4. Construir el contenido del archivo
        total_tickets = len(critical_lines) + len(high_lines) + len(medium_lines) + len(low_lines)
        progress_content = f"""# SRST Progress Tracker - {timestamp}

## Sesión Actual
**Nuevos tickets generados:** {len(self.tickets)}
**Total de tickets (incluyendo resueltos):** {total_tickets}

## Tickets por Prioridad

### 🚨 CRITICAL ({len(critical_lines)} tickets)
""" + ("\n".join(critical_lines) if critical_lines else "Ninguno") + """

### 🔥 HIGH ({len(high_lines)} tickets)
""" + ("\n".join(high_lines) if high_lines else "Ninguno") + """

### 📋 MEDIUM ({len(medium_lines)} tickets)
""" + ("\n".join(medium_lines) if medium_lines else "Ninguno") + """

### 📝 LOW ({len(low_lines)} tickets)
""" + ("\n".join(low_lines) if low_lines else "Ninguno") + """

## Recomendación de Sesión
**Empezar con:** El primer ticket CRITICAL no resuelto.
"""
        progress_file.write_text(progress_content, encoding='utf-8')

    def _get_resolved_ticket_lines(self) -> List[str]:
        """Lee SRST_PROGRESS.md y extrae las líneas de los tickets resueltos."""
        progress_file = self.base_path / "SRST_PROGRESS.md"
        resolved_lines: List[str] = []
        if not progress_file.exists():
            return resolved_lines

        content = progress_file.read_text(encoding='utf-8')
        # Patrón para encontrar cualquier línea que empiece con el marcador de ticket resuelto
        resolved_pattern = re.compile(r"^\s*-\s*\[(x|✅)\].*$", re.MULTILINE)
        
        matches = resolved_pattern.findall(content)
        
        # Para obtener las líneas completas, necesitamos un enfoque diferente
        for line in content.splitlines():
            # Ajuste del regex para ser menos sensible a espacios/marcadores exactos
            if re.match(r"^\s*-\s*\[[x✅]\].*", line):
                resolved_lines.append(line)

        print(f"✅ Encontrados {len(resolved_lines)} tickets previamente resueltos.")
        return resolved_lines

    def _get_max_ticket_id(self) -> int:
        """Encuentra el ID de ticket más alto en el sistema."""
        max_id = 0
        ticket_dir = self.base_path / "SRST_TICKETS"
        if ticket_dir.exists():
            for item in ticket_dir.iterdir():
                if item.is_dir() and item.name.startswith("SRST-"):
                    try:
                        ticket_id = int(item.name.split('-')[1])
                        if ticket_id > max_id:
                            max_id = ticket_id
                    except (ValueError, IndexError):
                        continue
        
        progress_file = self.base_path / "SRST_PROGRESS.md"
        if progress_file.exists():
            content = progress_file.read_text(encoding='utf-8')
            ids = re.findall(r"SRST-(\d{3,})", content)
            for str_id in ids:
                ticket_id = int(str_id)
                if ticket_id > max_id:
                    max_id = ticket_id
        return max_id

    def run_triage(self) -> None:
        """Ejecuta el triage completo del SRST de forma stateful."""
        print("🚨 INICIANDO TRIAGE AUTOMÁTICO SRST (STATEFUL)...")
        
        self._recreate_ticket_directory()
        
        # Cargar las líneas de los tickets resueltos y extraer sus scopes
        self.resolved_lines = self._get_resolved_ticket_lines()
        resolved_scopes: Set[str] = set()
        scope_pattern = re.compile(r"\(Test: (.*?)\)")
        for line in self.resolved_lines:
            match = scope_pattern.search(line)
            if match:
                resolved_scopes.add(match.group(1).strip())
        
        try:
            output = self.run_pytest_collect()
            if not output or not output.strip():
                print("⚠️ No se obtuvo salida de pytest o la salida está vacía. El triage no puede continuar.")
                self.tickets = []
                self.generate_progress_tracker() # Genera un reporte vacío para mantener consistencia
                print("✅ Triage finalizado: No se encontraron nuevos errores.")
                return
        except Exception as e:
            print(f"❌ Error crítico durante la ejecución de pytest: {e}")
            return
        
        print("🔍 Analizando salida de pytest...")
        all_potential_tickets = self.parse_pytest_output(output)
        
        print(f"🔎 Encontrados {len(all_potential_tickets)} errores potenciales en la salida de pytest.")
        
        self.tickets = [
            ticket for ticket in all_potential_tickets 
            if ticket.test_scope not in resolved_scopes
        ]
        
        print(f"✨ {len(all_potential_tickets) - len(self.tickets)} errores ya resueltos fueron ignorados.")

        if not self.tickets:
            print("🎉 ¡No hay nuevos errores que requieran tickets! El triage ha finalizado.")
            self.generate_progress_tracker()
            return

        self.ticket_counter = self._get_max_ticket_id() + 1
        
        print(f"🎫 Generando {len(self.tickets)} nuevos tickets individuales...")
        for ticket in self.tickets:
            ticket.id = f"SRST-{self.ticket_counter:03d}"
            self.generate_ticket_file(ticket)
            self.ticket_counter += 1
        
        print("📋 Actualizando SRST_PROGRESS.md...")
        self.generate_progress_tracker()
        
        stats: Dict[str, Any] = {
            "total_tickets": len(self.tickets),
            "critical": len([t for t in self.tickets if t.priority == ErrorPriority.CRITICAL]),
            "high": len([t for t in self.tickets if t.priority == ErrorPriority.HIGH]),
            "medium": len([t for t in self.tickets if t.priority == ErrorPriority.MEDIUM]),
            "low": len([t for t in self.tickets if t.priority == ErrorPriority.LOW]),
            "categories": sorted(list(set(t.category.value for t in self.tickets))),
            "estimated_total_time": sum(t.estimated_time for t in self.tickets)
        }
        
        print(f"""
✅ TRIAGE COMPLETADO
==================
📊 Nuevos tickets: {stats['total_tickets']}
🚨 Critical: {stats['critical']}
🔥 High: {stats['high']}
📋 Medium: {stats['medium']}
📝 Low: {stats['low']}
⏱️ Tiempo estimado (nuevos): {stats['estimated_total_time']} minutos
📁 Categorías: {', '.join(stats['categories'])}

🎯 PRÓXIMOS PASOS:
1. Revisar SRST_PROGRESS.md
2. Seleccionar un ticket para trabajar.
""")

if __name__ == "__main__":
    triage = SRSTTriage()
    triage.run_triage()
