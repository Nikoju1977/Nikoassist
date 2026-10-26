"""Sentinel-governed nanoMuse tool for an optional OpenMontage job handoff."""
from __future__ import annotations

import json
from typing import Any

from pydantic import Field
from nanomuse.schema import RiskLevel, ToolResult
from nanomuse.tools.base import BaseTool, CallAssessment
from nanomuse.nikoassist.openmontage import (
    OpenMontageError, prepare, preflight, status,
)


class OpenMontageTool(BaseTool):
    name: str = "openmontage"
    description: str = (
        "Connecteur OpenMontage : liste les pipelines de production vidéo, "
        "prépare un brief dans un projet OpenMontage séparé et consulte son état. "
        "Aucun rendu ni téléchargement automatique. La préparation nécessite "
        "l'approbation Sentinel. Un agent OpenMontage distinct réalise le rendu."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "prepare", "status"],
                "description": "list=état/pipelines, prepare=créer un brief, status=vérifier un projet",
            },
            "pipeline": {"type": "string", "description": "Nom exact du pipeline listé"},
            "brief": {"type": "string", "description": "But et contraintes de la vidéo"},
            "project": {"type": "string", "description": "Identifiant unique minuscules/tirets"},
            "duration_seconds": {"type": "integer", "minimum": 5, "maximum": 1800},
        },
        "required": ["action"],
    }
    risk: RiskLevel = RiskLevel.MODERATE
    app: Any = Field(exclude=True)

    def assess(self, args: dict[str, Any]) -> CallAssessment:
        operation = args.get("action")
        return CallAssessment(
            risk=RiskLevel.SENSITIVE if operation == "prepare" else RiskLevel.SAFE,
            summary=f"OpenMontage : {str(operation)[:32]} (rendu non automatique)",
        )

    async def execute(
        self, action: str = "list", pipeline: str = "", brief: str = "",
        project: str = "", duration_seconds: int = 60, **_: Any,
    ) -> ToolResult:
        try:
            if action == "list":
                result = preflight()
            elif action == "prepare":
                result = prepare(
                    pipeline=pipeline, brief=brief, project=project,
                    duration_seconds=duration_seconds,
                )
            elif action == "status":
                result = status(project=project)
            else:
                return ToolResult.fail("Action OpenMontage inconnue.")
            return ToolResult(output=json.dumps(result, ensure_ascii=False))
        except OpenMontageError as exc:
            return ToolResult.fail(str(exc))
        except Exception as exc:
            return ToolResult.fail(f"OpenMontage indisponible ({type(exc).__name__}).")
