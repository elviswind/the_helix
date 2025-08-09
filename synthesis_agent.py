#!/usr/bin/env python3
"""
Synthesis Agent for AR System v3.0

This agent generates a balanced, final report by synthesizing the approved
Thesis and Antithesis dossiers into a single coherent narrative.
"""

import json
import uuid
import requests
import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from models import SessionLocal, Job, EvidenceDossier, SynthesisReport, LLMRequest, LLMRequestStatus, LLMRequestType
from celery_app import celery_app
from logging_config import get_file_logger

class SynthesisAgent:
    """Agent responsible for generating the final balanced report"""
    
    def __init__(self):
        self.llm_url = "http://192.168.1.15:11434/api/generate"
        self.model = "gemma3:27b"
        self.logger = get_file_logger("agent.synthesis", "logs/agent.log")
    
    def generate_synthesis_prompt(self, thesis_dossier: EvidenceDossier, antithesis_dossier: EvidenceDossier) -> str:
        """Generate the prompt for the synthesis LLM call"""
        
        # Extract key information from both dossiers
        thesis_mission = thesis_dossier.mission
        antithesis_mission = antithesis_dossier.mission
        thesis_summary = thesis_dossier.summary_of_findings or "No summary provided"
        antithesis_summary = antithesis_dossier.summary_of_findings or "No summary provided"
        
        # Get evidence items from both dossiers
        thesis_evidence = [f"- {item.title}: {item.content} (Source: {item.source})" 
                          for item in thesis_dossier.evidence_items]
        antithesis_evidence = [f"- {item.title}: {item.content} (Source: {item.source})" 
                              for item in antithesis_dossier.evidence_items]
        
        # Get research plan steps with proxy hypotheses
        thesis_steps = []
        for step in thesis_dossier.research_plan.steps:
            step_info = f"Step {step.step_number}: {step.description}"
            if step.proxy_hypothesis:
                step_info += f"\n  Proxy Hypothesis: {json.dumps(step.proxy_hypothesis, indent=2)}"
            thesis_steps.append(step_info)
        
        antithesis_steps = []
        for step in antithesis_dossier.research_plan.steps:
            step_info = f"Step {step.step_number}: {step.description}"
            if step.proxy_hypothesis:
                step_info += f"\n  Proxy Hypothesis: {json.dumps(step.proxy_hypothesis, indent=2)}"
            antithesis_steps.append(step_info)
        
        prompt = f"""You are a Synthesis Agent tasked with creating a balanced, final report from two opposing research dossiers.

THESIS DOSSIER:
Mission: {thesis_mission}
Summary: {thesis_summary}
Research Steps:
{chr(10).join(thesis_steps)}
Evidence:
{chr(10).join(thesis_evidence)}

ANTITHESIS DOSSIER:
Mission: {antithesis_mission}
Summary: {antithesis_summary}
Research Steps:
{chr(10).join(antithesis_steps)}
Evidence:
{chr(10).join(antithesis_evidence)}

Your task is to write a single, balanced executive summary that:

1) States the core thesis argument clearly and concisely
2) States the core antithesis argument clearly and concisely
3) Explicitly highlights key points of conflict and contradiction between the two cases
4) Provides a final, nuanced assessment based ONLY on the evidence and citations present in the provided dossiers
5) Acknowledges any proxy hypotheses used and their logical soundness
6) Maintains intellectual honesty by presenting both sides fairly

Format your response as a well-structured report with clear sections. Use markdown formatting for readability. Do not introduce any external information or assumptions not present in the provided dossiers.

Your response should be comprehensive but concise, typically 800-1200 words."""

        return prompt
    
    def call_llm(self, prompt: str) -> str:
        """Call the LLM to generate the synthesis report"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        
        try:
            response = requests.post(self.llm_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            self.logger.error("LLM call failed: %s", e)
            raise Exception(f"LLM call failed: {str(e)}")
    
    def synthesize_dossiers(self, job_id: str) -> str:
        """Main synthesis method that processes both dossiers and generates the final report"""
        
        db = SessionLocal()
        try:
            # Get the job and both dossiers
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise Exception(f"Job {job_id} not found")
            
            thesis_dossier = db.query(EvidenceDossier).filter(
                EvidenceDossier.job_id == job_id,
                EvidenceDossier.dossier_type == "THESIS"
            ).first()
            
            antithesis_dossier = db.query(EvidenceDossier).filter(
                EvidenceDossier.job_id == job_id,
                EvidenceDossier.dossier_type == "ANTITHESIS"
            ).first()
            
            if not thesis_dossier or not antithesis_dossier:
                raise Exception("Both thesis and antithesis dossiers must exist")
            
            if thesis_dossier.status.value != "APPROVED" or antithesis_dossier.status.value != "APPROVED":
                raise Exception("Both dossiers must be approved before synthesis")
            
            # Generate the synthesis prompt
            prompt = self.generate_synthesis_prompt(thesis_dossier, antithesis_dossier)
            
            # Log the LLM request
            llm_request = LLMRequest(
                id=f"llm-{uuid.uuid4().hex[:8]}",
                job_id=job_id,
                request_type=LLMRequestType.SYNTHESIS,
                status=LLMRequestStatus.IN_PROGRESS,
                prompt=prompt,
                started_at=datetime.utcnow()
            )
            db.add(llm_request)
            db.commit()
            
            # Call the LLM
            synthesis_content = self.call_llm(prompt)
            
            # Update LLM request
            llm_request.status = LLMRequestStatus.COMPLETED
            llm_request.response = synthesis_content
            llm_request.completed_at = datetime.utcnow()
            
            # Save the synthesis report
            synthesis_report = SynthesisReport(
                id=f"syn-{uuid.uuid4().hex[:8]}",
                job_id=job_id,
                content=synthesis_content
            )
            db.add(synthesis_report)
            db.commit()
            
            return synthesis_content
            
        except Exception as e:
            # Log the error in LLM request if it exists
            if 'llm_request' in locals():
                llm_request.status = LLMRequestStatus.FAILED
                llm_request.error_message = str(e)
                llm_request.completed_at = datetime.utcnow()
                db.commit()
            
            self.logger.error("Synthesis failed for job %s: %s", job_id, e)
            raise e
        finally:
            db.close()

# Create the synthesis agent instance
synthesis_agent = SynthesisAgent()

@celery_app.task(bind=True)
def synthesis_agent_task(self, job_id: str):
    """Celery task for the synthesis agent"""
    
    try:
        logger = get_file_logger("agent.synthesis", "logs/agent.log")
        logger.info("Starting synthesis for job %s", job_id)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Generating synthesis report...'}
        )
        
        # Generate the synthesis report
        synthesis_content = synthesis_agent.synthesize_dossiers(job_id)
        
        logger.info("Synthesis completed for job %s", job_id)
        
        # Update task state
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Synthesis completed',
                'job_id': job_id,
                'content_length': len(synthesis_content)
            }
        )
        
        return {
            'status': 'SUCCESS',
            'job_id': job_id,
            'content_length': len(synthesis_content)
        }
        
    except Exception as e:
        logger = get_file_logger("agent.synthesis", "logs/agent.log")
        logger.error("Synthesis failed for job %s: %s", job_id, e)
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Synthesis failed',
                'error': str(e)
            }
        )
        
        raise e

if __name__ == "__main__":
    # Test the synthesis agent
    import sys
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        result = synthesis_agent_task.delay(job_id)
        logger = get_file_logger("agent.synthesis", "logs/agent.log")
        logger.info("Synthesis task queued: %s", result.id)
    else:
        logger = get_file_logger("agent.synthesis", "logs/agent.log")
        logger.warning("Usage: python synthesis_agent.py <job_id>")