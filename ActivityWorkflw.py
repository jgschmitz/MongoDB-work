from temporalio import workflow, activity

@workflow.defn
class DocumentClassificationWorkflow:
    @workflow.run
    async def run(self, document_id: str):
        # Step 1: AI Agent processes the document
        classification_result = await workflow.execute_activity(
            classify_document,
            document_id,
            start_to_close_timeout=10
        )
        
        # Step 2: Check confidence level
        if classification_result['confidence'] < 0.8:
            # Step 3: Wait for human-in-the-loop decision
            human_decision = await workflow.wait_for_signal("human_approval")
            
            if human_decision == "approved":
                await workflow.execute_activity(
                    finalize_classification,
                    classification_result,
                    start_to_close_timeout=5
                )
            elif human_decision == "rejected":
                await workflow.execute_activity(
                    escalate_issue,
                    document_id,
                    start_to_close_timeout=5
                )
        else:
            # Auto-approve if confidence is high
            await workflow.execute_activity(
                finalize_classification,
                classification_result,
                start_to_close_timeout=5
            )
