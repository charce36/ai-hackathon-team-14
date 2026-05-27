from publisher_support.llm.schemas import RCALLMOutput, PatchFileLLM


def test_rca_output_fills_missing_files_and_reasoning():
    partial = {
        "root_cause": "Lag de replicación MySQL RW→RO alto",
        "summary": "Datos viejos en panel por lag de replicación",
        "confidence": 0.9,
        "eta_minutes": 10,
        "patch_id": "fix-mysql-replication",
        "description": "Forzar catch-up de replicación",
    }
    result = RCALLMOutput.model_validate(partial)
    assert result.reasoning
    assert result.publisher_summary
    assert len(result.files) >= 1
    assert result.files[0].content.strip()
