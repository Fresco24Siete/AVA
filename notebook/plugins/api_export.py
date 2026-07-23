"""
INSTRUCTOR, ver jupyterhub_config.py):
    METRICS_API_URL    ej. http://backend_go:8080/internal/metrics
    METRICS_API_TOKEN  token de servicio compartido entre jupyterhub y el backend
    ENVIAR_AL_BACKEND  "true" o "false" (por defecto "false")
"""
import json
import os
import traceback

import requests

from nbgrader.api import MissingEntry, Gradebook
from nbgrader.plugins import ExportPlugin


class ApiExportPlugin(ExportPlugin):
    """Envía notas de nbgrader al backend Go en vez de escribir a Postgres
    directamente."""

    def export(self, gradebook: Gradebook) -> None:
        enviar_backend = os.environ.get('ENVIAR_AL_BACKEND', 'false').lower() in ('true', '1', 'yes')
        api_url = os.environ.get('METRICS_API_URL')
        api_token = os.environ.get('METRICS_API_TOKEN')
        curso_id = os.environ.get('CURSO_ID')

        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
        }

        for assignment in gradebook.assignments:
            cuadernillo_codigo = assignment.name  # tu backend lo resuelve a cuadernillo_id

            for student in gradebook.students:
                try:
                    submission = gradebook.find_submission(
                        assignment.name, student.id)
                except MissingEntry:
                    continue  # aún no entrega nada

                puntaje_total = max(
                    0.0, submission.score - submission.late_submission_penalty
                )

                ejercicios = []
                for notebook in submission.notebooks:
                    for idx, grade in enumerate(notebook.grades, 1):
                        ejercicios.append({
                            'codigo_celda': grade.name,       # p.ej. "ejercicio_1"
                            'orden': idx,
                            'descripcion': grade.name,
                            'puntos_obtenidos': grade.score,
                            'puntos_maximos': grade.max_score,
                            'aprobado': grade.max_score > 0 and grade.score >= grade.max_score,
                        })

                payload = {
                    'curso_id': curso_id,
                    'cuadernillo_codigo': cuadernillo_codigo,
                    'estudiante_id': student.id,
                    'estado': 'terminado',
                    'fecha_fin': str(submission.timestamp) if submission.timestamp else None,
                    'puntaje_total': puntaje_total,
                    'puntaje_maximo': assignment.max_score,
                    'ejercicios': ejercicios,
                }

                if not enviar_backend:
                    self.log.info(
                        "[api_export] ENVIAR_AL_BACKEND=false (Simulación activada). Exportación final capturada:\n%s",
                        json.dumps(payload, indent=2, ensure_ascii=False)
                    )
                    continue

                if not api_url or not api_token:
                    self.log.error(
                        "METRICS_API_URL / METRICS_API_TOKEN no configurados; no se puede exportar."
                    )
                    continue

                try:
                    resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
                    if resp.status_code >= 400:
                        self.log.error(
                            "Backend rechazó métricas de %s/%s: %s %s",
                            cuadernillo_codigo, student.id, resp.status_code, resp.text,
                        )
                except requests.RequestException:
                    self.log.error(
                        "Error de red exportando %s/%s: %s",
                        cuadernillo_codigo, student.id, traceback.format_exc(),
                    )