import math
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.database_models import DecisionLog
from backend.app.engines.core_twin import get_or_create_twin, update_twin_state
from backend.app.schemas import schemas

SCENARIOS = {
    "production_outage": {
        "id": "production_outage",
        "title": "The Production Outage Panic",
        "description": "A business-critical payment processing API is dropping 45% of customer transactions. Alerts are firing. You need to triage and resolve the issue under intense time pressure without causing data corruption.",
        "steps": [
            {
                "step_id": 1,
                "situation": "Multiple customer payment requests are failing with HTTP 500 errors. The support channel is flooded. What is your first step?",
                "clues": [
                    {"id": "logs", "title": "Inspect Microservice Logs", "content": "Database connection pool saturated with 150 pending transactions waiting for database locks."},
                    {"id": "infra", "title": "Check Infrastructure Status", "content": "CPU usage is 18%, memory is 42% (perfectly normal)."},
                    {"id": "git", "title": "Check Git Deployment History", "content": "A deployment happened 15 minutes ago by another dev, altering default database pool timeouts from 30s to 5s."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Reboot all API containers immediately to clear connection pool memory state.",
                        "biases": {"impulsiveness": 0.8, "availability_heuristic": 0.7, "analytical_thinking": 0.2, "risk_tolerance": 0.6},
                        "risk_level": "medium",
                        "feedback": "Containers rebooted, but database connection pool saturated again within 30 seconds. Outage continues."
                    },
                    {
                        "id": "B",
                        "text": "Roll back the git deployment immediately.",
                        "biases": {"confirmation_bias": 0.5, "risk_tolerance": 0.7, "analytical_thinking": 0.4},
                        "risk_level": "high",
                        "feedback": "Deployment rolled back, but database sessions are still locked by orphaned connection threads. Outage persists."
                    },
                    {
                        "id": "C",
                        "text": "Analyze active database connections to identify lock origins.",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.3, "impulsiveness": 0.1},
                        "risk_level": "low",
                        "feedback": "You find a long-running migrator transaction holding an exclusive lock on the 'transactions' table."
                    }
                ]
            },
            {
                "step_id": 2,
                "situation": "You've identified that a background data-migration job (running on a backup thread) is holding a lock on the 'transactions' table. The migration has been running for 4.2 hours and is 90% complete. What do you do?",
                "clues": [
                    {"id": "migration_code", "title": "Inspect Migration Script", "content": "The script runs within a single large transaction block. Terminating it forcefully will trigger a rollback that may take up to an hour."},
                    {"id": "traffic", "title": "Analyze Live Traffic Patterns", "content": "90% of failures are retries. Rate-limiting incoming retries would alleviate server overload."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Kill the PostgreSQL process ID (PID) of the migration job immediately.",
                        "biases": {"impulsiveness": 0.9, "risk_tolerance": 0.9, "analytical_thinking": 0.1},
                        "risk_level": "high",
                        "feedback": "Process terminated. Postgres starts rolling back the uncommitted transaction. Database remains locked and unresponsive."
                    },
                    {
                        "id": "B",
                        "text": "Enable temporary API rate-limiting and wait for the migration to finish gracefully (estimated 15 minutes).",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.4, "impulsiveness": 0.2},
                        "risk_level": "low",
                        "feedback": "Temporary rate-limits reduce database load. 12 minutes later, the migration completes, locks release, and traffic flows normally."
                    },
                    {
                        "id": "C",
                        "text": "Pause the database server and perform an emergency database scaling operation.",
                        "biases": {"bandwagon_effect": 0.6, "risk_tolerance": 0.8, "analytical_thinking": 0.3},
                        "risk_level": "high",
                        "feedback": "Database restarted and instance size scaled up. However, upon boot, Postgres still enters crash recovery to roll back the migrator task, keeping locks held."
                    }
                ]
            },
            {
                "step_id": 3,
                "situation": "With the database locks finally released and transactions flowing again, how do you prevent this issue in the post-mortem phase?",
                "clues": [
                    {"id": "db_config", "title": "Inspect DB Locks Configuration", "content": "Postgres default lock wait timeout is unlimited, meaning a migrator will block all read/write clients forever if it gets stuck."},
                    {"id": "docs", "title": "Review Engineering Playbook", "content": "Playbook suggests always wrapping schema migrations in dry-run checks and locking timeouts."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Deploy a quick patch to set lock_timeout = 10000 (10s) globally on the database.",
                        "biases": {"impulsiveness": 0.6, "risk_tolerance": 0.6, "analytical_thinking": 0.5},
                        "risk_level": "medium",
                        "feedback": "Patch deployed. Fast and dirty, but setting global database timeouts might break valid long-running analytical queries later."
                    },
                    {
                        "id": "B",
                        "text": "Establish a policy: all schema migrations must run in tiny batched transactions with dedicated statement timeouts.",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.2, "impulsiveness": 0.2},
                        "risk_level": "low",
                        "feedback": "Perfect. Migrations are now decoupled and non-blocking, ensuring safe and resilient continuous delivery."
                    },
                    {
                        "id": "C",
                        "text": "Upgrade the database replica count and blame the cloud provider's network delay in the incident report.",
                        "biases": {"confirmation_bias": 0.8, "overconfidence": 0.7, "analytical_thinking": 0.2},
                        "risk_level": "low",
                        "feedback": "Incident report closed, but core locking issue is unaddressed. High likelihood of recurrence."
                    }
                ]
            }
        ]
    },
    "legacy_refactoring": {
        "id": "legacy_refactoring",
        "title": "The Legacy Refactoring Trap",
        "description": "Your core subscription billing engine is 8 years old, written in procedural PHP. Your team has spent 9 months refactoring it to a microservices architecture. It has blown past its budget, is still buggy, and is delaying crucial new features.",
        "steps": [
            {
                "step_id": 1,
                "situation": "The business demands that you ship 'Enterprise Custom Tiers' in 4 weeks. Your refactored billing service is only 75% complete and is failing edge-case tax audits. The team is exhausted. What do you do?",
                "clues": [
                    {"id": "budget", "title": "Check Budget Spent", "content": "95% of the refactoring budget has been exhausted. Sunk cost is $120,000."},
                    {"id": "diff", "title": "Examine Code Complexity", "content": "The legacy billing file is 14,000 lines long, but handles custom enterprise tiers using simple database column overrides."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Double down: pause all new feature requests and commit 100% team bandwidth to complete the refactored billing microservice.",
                        "biases": {"sunk_cost_fallacy": 0.9, "risk_tolerance": 0.7, "analytical_thinking": 0.3},
                        "risk_level": "high",
                        "feedback": "You commit more resources, but the complexity of edge-case tax calculations continues to push back completion. The business misses the custom tiers deadline."
                    },
                    {
                        "id": "B",
                        "text": "Implement the 'Enterprise Custom Tiers' inside the legacy engine directly as a fast patch, while keeping the refactor on a low-priority background thread.",
                        "biases": {"analytical_thinking": 0.8, "risk_tolerance": 0.4, "sunk_cost_fallacy": 0.1},
                        "risk_level": "low",
                        "feedback": "Feature shipped on time using legacy overrides. Business objectives met, and team gets breathing room to properly solve the refactoring challenges."
                    },
                    {
                        "id": "C",
                        "text": "Hire an external agency to write the remaining 25% of the refactored microservice.",
                        "biases": {"sunk_cost_fallacy": 0.8, "bandwagon_effect": 0.5, "analytical_thinking": 0.4},
                        "risk_level": "medium",
                        "feedback": "Agency onboarded. They take 3 weeks just to understand the architecture, exceeding budget, and deliver code that still fails tax checks."
                    }
                ]
            },
            {
                "step_id": 2,
                "situation": "A junior engineer suggests scrapping the refactored billing service altogether and using a third-party billing platform (e.g. Stripe Billing) to handle all custom and standard tiers, which would replace 90% of local code.",
                "clues": [
                    {"id": "cost", "title": "Review Third-Party Fees", "content": "Stripe charges 0.5% per invoice. Your current transaction volume means transaction fees will cost $4,000/month, but saves 1 full-time dev salary ($10,000/month)."},
                    {"id": "migration", "title": "Examine Migration Effort", "content": "Integrating Stripe Billing takes 3 weeks of API work and supports all tax edge-cases automatically."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Reject third-party tools. 'We spent 9 months building our custom system, we should not throw away our hard work.'",
                        "biases": {"sunk_cost_fallacy": 1.0, "confirmation_bias": 0.8, "analytical_thinking": 0.2},
                        "risk_level": "medium",
                        "feedback": "Refuse to migrate. The custom billing engine drags on, consuming developer maintenance hours indefinitely."
                    },
                    {
                        "id": "B",
                        "text": "Initiate a migration to Stripe Billing, writing off the 9-month refactor as a learning experience.",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.5, "sunk_cost_fallacy": 0.0},
                        "risk_level": "low",
                        "feedback": "Migration successfully completed in 3 weeks. Developer workload drops, allowing focus on core product features."
                    },
                    {
                        "id": "C",
                        "text": "Build a wrapper that tries to sync the half-finished custom microservice with Stripe Billing in parallel.",
                        "biases": {"confirmation_bias": 0.7, "risk_tolerance": 0.8, "sunk_cost_fallacy": 0.6},
                        "risk_level": "high",
                        "feedback": "Sync complexity leads to double-billing bugs and severe customer complaints. High risk realized."
                    }
                ]
            },
            {
                "step_id": 3,
                "situation": "After resolving the refactoring dilemma, you need to set up a legacy refactoring decision framework. How do you assess future 're-write' proposals?",
                "clues": [
                    {"id": "industry", "title": "Check Refactoring Standards", "content": "Industry data shows 70% of complete system rewrites exceed time estimations by over 100%."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Mandate that no rewrites are allowed. All legacy systems must be patched forever.",
                        "biases": {"status_quo_bias": 0.9, "risk_tolerance": 0.1, "analytical_thinking": 0.3},
                        "risk_level": "low",
                        "feedback": "Technical debt accumulates until the application becomes completely unmaintainable years later."
                    },
                    {
                        "id": "B",
                        "text": "Implement a Strangler Fig Application Pattern rule: all rewrites must be done incrementally, feature by feature, behind a routing proxy.",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.3},
                        "risk_level": "low",
                        "feedback": "Excellent policy. Promotes iterative, low-risk modular modernization."
                    },
                    {
                        "id": "C",
                        "text": "Approve rewrites based on developer excitement and stack modernization desires.",
                        "biases": {"bandwagon_effect": 0.8, "overconfidence": 0.6, "analytical_thinking": 0.2},
                        "risk_level": "high",
                        "feedback": "Leading to constant churn of half-finished frameworks and unstable architectures."
                    }
                ]
            }
        ]
    },
    "architecture_choice": {
        "id": "architecture_choice",
        "title": "The Hype-Driven Architecture Dilemma",
        "description": "A new decentralized serverless database technology is trending. It promises 10x write performance. The development team is highly eager to adopt it for a standard relational Customer Relationship Management (CRM) project.",
        "steps": [
            {
                "step_id": 1,
                "situation": "The CRM project requires standard complex relational queries (e.g. joins, nested filters, transactional safety). The team wants to use the new serverless DB. What is your evaluation strategy?",
                "clues": [
                    {"id": "spec", "title": "Check Database Spec", "content": "The database is non-relational, lacks transactional ACID guarantees, and doesn't support joins natively."},
                    {"id": "community", "title": "Evaluate Ecosystem Activity", "content": "The database has only 1.2k stars on GitHub and has zero production case-studies outside of developer blogs."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Adopt the serverless database to make the stack modern and attract talent.",
                        "biases": {"bandwagon_effect": 1.0, "risk_tolerance": 0.9, "analytical_thinking": 0.1},
                        "risk_level": "high",
                        "feedback": "Database adopted. The team struggles to implement relational joins in application code, dragging down performance and velocity."
                    },
                    {
                        "id": "B",
                        "text": "Stick with PostgreSQL. Relational databases are a proven fit for CRM workloads.",
                        "biases": {"analytical_thinking": 0.8, "risk_tolerance": 0.2, "bandwagon_effect": 0.1},
                        "risk_level": "low",
                        "feedback": "PostgreSQL adopted. Joins and queries are executed in microseconds with solid transactional integrity."
                    },
                    {
                        "id": "C",
                        "text": "Run a 2-day hackathon benchmark comparing PostgreSQL with the new database on CRM query shapes.",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.4, "bandwagon_effect": 0.2},
                        "risk_level": "low",
                        "feedback": "Benchmark reveals that while writes are fast, complex reads are 25x slower due to manual application joins. The team agrees to stick with SQL."
                    }
                ]
            },
            {
                "step_id": 2,
                "situation": "Your choice of PostgreSQL is finalized, but the team now wants to implement a highly complex microservices architecture (splitting CRM into 12 services) with Kubernetes orchestration, for a system expected to serve 500 active users.",
                "clues": [
                    {"id": "ops", "title": "Analyze Ops Overhead", "content": "Managing Kubernetes for a small user base consumes 40% of operations capacity. A single monolithic backend takes 5% of ops capacity."},
                    {"id": "perf_scale", "title": "Check Load Projections", "content": "500 active users will produce peak load of 10 requests per second, which a single virtual machine ($10/month) can handle at 5% CPU."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Approve Kubernetes microservices. 'We must build for scale from day one.'",
                        "biases": {"bandwagon_effect": 0.9, "overconfidence": 0.8, "analytical_thinking": 0.2},
                        "risk_level": "high",
                        "feedback": "System is highly complex. Developers spend more time fixing Kubernetes network configurations than shipping product features."
                    },
                    {
                        "id": "B",
                        "text": "Build a modular monolith and host it on a single Docker-compose virtual machine with automated backups.",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.3, "bandwagon_effect": 0.1},
                        "risk_level": "low",
                        "feedback": "System is simple, robust, and fast. Operational overhead is virtually zero, allowing developers to ship features daily."
                    },
                    {
                        "id": "C",
                        "text": "Adopt serverless functions (lambda) for every single API endpoint.",
                        "biases": {"bandwagon_effect": 0.7, "risk_tolerance": 0.6, "analytical_thinking": 0.4},
                        "risk_level": "medium",
                        "feedback": "Lambda functions suffer from cold starts and database connection saturation due to lack of a shared pool, causing random lag spikes."
                    }
                ]
            },
            {
                "step_id": 3,
                "situation": "Months later, the project is a success. The team wants to incorporate machine learning (LLM-based lead scoring). How do you integrate it?",
                "clues": [
                    {"id": "ml_needs", "title": "Evaluate ML Requirements", "content": "A simple heuristic scoring system (assigning points based on job title/company size) works in 95% of cases. Training an LLM classifier costs $15,000 in GPU time."}
                ],
                "options": [
                    {
                        "id": "A",
                        "text": "Deploy a local PyTorch neural network lead classifier.",
                        "biases": {"bandwagon_effect": 0.8, "overconfidence": 0.7, "analytical_thinking": 0.3},
                        "risk_level": "medium",
                        "feedback": "Neural network works, but requires continuous fine-tuning and debugging, creating support overhead."
                    },
                    {
                        "id": "B",
                        "text": "Start with a simple relational database SQL query scoring heuristic, and only build ML models if data shows the heuristic is failing.",
                        "biases": {"analytical_thinking": 0.9, "risk_tolerance": 0.2, "bandwagon_effect": 0.1},
                        "risk_level": "low",
                        "feedback": "The heuristic works perfectly, takes 2 hours to code, costs zero dollars, and is instantly transparent to business analysts."
                    },
                    {
                        "id": "C",
                        "text": "Integrate a paid third-party enterprise AI CRM platform API.",
                        "biases": {"risk_tolerance": 0.5, "confirmation_bias": 0.6, "analytical_thinking": 0.4},
                        "risk_level": "low",
                        "feedback": "API works but adds monthly subscription fees, reducing margins for a feature that could be solved locally."
                    }
                ]
            }
        ]
    }
}

def get_scenarios_metadata() -> List[Dict[str, Any]]:
    """Returns a list of scenarios without the hidden scoring weights/biases."""
    result = []
    for s_id, scenario in SCENARIOS.items():
        steps_clean = []
        for step in scenario["steps"]:
            options_clean = []
            for opt in step["options"]:
                options_clean.append({
                    "id": opt["id"],
                    "text": opt["text"],
                    "risk_level": opt["risk_level"],
                    "feedback": opt["feedback"]
                })
            steps_clean.append({
                "step_id": step["step_id"],
                "situation": step["situation"],
                "clues": step["clues"],
                "options": options_clean
            })
        result.append({
            "id": scenario["id"],
            "title": scenario["title"],
            "description": scenario["description"],
            "steps": steps_clean
        })
    return result

def evaluate_arena_run(db: Session, user_id: int, submission: schemas.ArenaScenarioSubmit) -> Dict[str, Any]:
    """Calculates cognitive indicators from an Arena run, logs a decision entry,
    and blends results into the user's twin state.
    """
    scenario_id = submission.scenario_id
    if scenario_id not in SCENARIOS:
        raise ValueError("Invalid scenario identifier.")
        
    scenario = SCENARIOS[scenario_id]
    steps_lookup = {step["step_id"]: step for step in scenario["steps"]}
    
    # Track metrics accumulators
    analytical_sum = 0.0
    risk_sum = 0.0
    impulsiveness_sum = 0.0
    sunk_cost_sum = 0.0
    confirmation_bias_sum = 0.0
    confidence_sum = 0.0
    evidence_collected_count = 0
    total_clues_available = 0
    
    steps_feedback = []
    
    for user_step in submission.steps:
        step_id = user_step.step_id
        if step_id not in steps_lookup:
            continue
        step = steps_lookup[step_id]
        
        # Match option
        option_selected = user_step.option_selected
        matched_opt = next((o for o in step["options"] if o["id"] == option_selected), None)
        if not matched_opt:
            continue
            
        biases = matched_opt.get("biases", {})
        
        # Accumulate metrics
        analytical_sum += biases.get("analytical_thinking", 0.5)
        risk_sum += biases.get("risk_tolerance", 0.5)
        sunk_cost_sum += biases.get("sunk_cost_fallacy", 0.0)
        confirmation_bias_sum += biases.get("confirmation_bias", 0.0)
        
        # Clues ratio
        clues_collected = len(user_step.evidence_collected)
        clues_available = len(step["clues"])
        evidence_collected_count += clues_collected
        total_clues_available += clues_available
        
        # Impulsiveness scoring: based on time and lack of evidence
        # Under 10s is fast; lack of clues increases impulsiveness
        time_seconds = user_step.time_spent_seconds
        time_factor = max(0.0, 1.0 - (time_seconds / 15.0))  # 1.0 at 0s, 0.0 at 15s+
        evidence_ratio = (clues_collected / clues_available) if clues_available > 0 else 1.0
        step_impulsive = (0.7 * time_factor) + (0.3 * (1.0 - evidence_ratio))
        impulsiveness_sum += step_impulsive
        
        # Confirmation bias accumulation: if they selected option with confirmation bias
        # and collected fewer disconfirming clues
        confirmation_bias_sum += (1.0 - evidence_ratio) * 0.2
        
        # Confidence
        confidence_sum += user_step.confidence
        
        steps_feedback.append({
            "step_id": step_id,
            "situation_title": f"Step {step_id}",
            "choice_made": matched_opt["text"],
            "feedback": matched_opt["feedback"],
            "time_spent": round(time_seconds, 1),
            "clues_revealed": clues_collected
        })
        
    n_steps = len(submission.steps) or 1
    
    # Calculate averages
    avg_analytical = analytical_sum / n_steps
    avg_risk = risk_sum / n_steps
    avg_impulsive = min(1.0, max(0.0, impulsiveness_sum / n_steps))
    avg_sunk_cost = min(1.0, max(0.0, sunk_cost_sum / n_steps))
    avg_confirmation_bias = min(1.0, max(0.0, confirmation_bias_sum / n_steps))
    avg_confidence = confidence_sum / n_steps
    
    # Overconfidence calculation
    evidence_ratio_total = (evidence_collected_count / total_clues_available) if total_clues_available > 0 else 1.0
    avg_overconfidence = max(0.0, min(1.0, avg_confidence * (1.0 - evidence_ratio_total)))
    
    # Combine into a final score (0.0 to 1.0, higher is better decision quality)
    # High analytical, low impulsiveness, low overconfidence, low sunk cost => high decision score
    decision_score = (avg_analytical + (1.0 - avg_impulsive) + (1.0 - avg_overconfidence) + (1.0 - avg_sunk_cost)) / 4.0
    decision_score = round(max(0.1, min(0.98, decision_score)), 2)
    
    # Determine detected biases
    biases_detected = {}
    if avg_overconfidence > 0.5:
        biases_detected["overconfidence"] = {
            "severity": round(avg_overconfidence, 2),
            "description": "High self-reported confidence combined with low evidence collection."
        }
    if avg_impulsive > 0.6:
        biases_detected["impulsiveness"] = {
            "severity": round(avg_impulsive, 2),
            "description": "Decisions were made rapidly with minimal investigation of logs and clues."
        }
    if avg_sunk_cost > 0.5:
        biases_detected["sunk_cost"] = {
            "severity": round(avg_sunk_cost, 2),
            "description": "Doubled down on past resources spent rather than choosing the optimal forward path."
        }
    if avg_confirmation_bias > 0.5:
        biases_detected["confirmation_bias"] = {
            "severity": round(avg_confirmation_bias, 2),
            "description": "Relied heavily on quick assumptions without unlocking full available diagnostic insights."
        }
        
    metrics = {
        "analytical_thinking": round(avg_analytical, 2),
        "risk_tolerance": round(avg_risk, 2),
        "impulsiveness": round(avg_impulsive, 2),
        "sunk_cost": round(avg_sunk_cost, 2),
        "confirmation_bias": round(avg_confirmation_bias, 2),
        "overconfidence": round(avg_overconfidence, 2)
    }
    
    # Create descriptive feedback summary
    feedback_intro = f"Completed Cognitive Arena: **{scenario['title']}**.\n\n"
    if decision_score >= 0.8:
        feedback_intro += "Outstanding decision quality! You demonstrated systematic evidence collection, controlled risk management, and sound logical reasoning."
    elif decision_score >= 0.5:
        feedback_intro += "Solid performance, but there is room to improve. Pay attention to bias traps like jumping to conclusions or doubling down on spent costs."
    else:
        feedback_intro += "Caution: Cognitive biases heavily influenced your decisions. Review your diagnostic path and practice mitigation strategies."
        
    # Create the DecisionLog row
    evidence_names = [f"Step {s.step_id} Option {s.option_selected}" for s in submission.steps]
    log = DecisionLog(
        user_id=user_id,
        title=f"Arena: {scenario['title']}",
        description=f"Participated in the cognitive simulation scenario '{scenario['title']}'. Captured decision path and bias heuristics.",
        choice_made=f"Paths: " + ", ".join([f"Step {s.step_id}: {s.option_selected}" for s in submission.steps]),
        risk_level="high" if avg_risk > 0.6 else "low" if avg_risk < 0.3 else "medium",
        evidence_collected=evidence_names,
        bias_detected=biases_detected,
        decision_speed_seconds=sum(s.time_spent_seconds for s in submission.steps),
        confidence=avg_confidence,
        status="resolved",
        outcome=f"Scenario Score: {int(decision_score*100)}%.\n" + "\n".join([f"• {f['choice_made']}: {f['feedback']}" for f in steps_feedback])
    )
    db.add(log)
    db.commit()
    
    # Update twin state with Exponential Moving Average (EMA)
    twin = get_or_create_twin(db, user_id)
    profile = dict(twin.state.get("decision_profile", {
        "risk_tolerance": 0.5,
        "analytical_thinking": 0.5,
        "intuition": 0.5,
        "evidence_collection_speed": 0.5,
        "decision_speed": 0.5,
        "bias_index": 0.1,
        "consistency": 0.8,
        "tradeoff_handling": 0.5,
        "decision_confidence": 0.5
    }))
    
    # Calculate general bias index
    new_bias_index = len(biases_detected) / 4.0
    
    # Blend old and new profile scores (0.3 weight to the new run)
    alpha = 0.3
    profile["analytical_thinking"] = round((1 - alpha) * profile.get("analytical_thinking", 0.5) + alpha * avg_analytical, 3)
    profile["risk_tolerance"] = round((1 - alpha) * profile.get("risk_tolerance", 0.5) + alpha * avg_risk, 3)
    profile["decision_speed"] = round((1 - alpha) * profile.get("decision_speed", 0.5) + alpha * (1.0 - avg_impulsive), 3)
    profile["bias_index"] = round((1 - alpha) * profile.get("bias_index", 0.1) + alpha * new_bias_index, 3)
    profile["decision_confidence"] = round((1 - alpha) * profile.get("decision_confidence", 0.5) + alpha * avg_confidence, 3)
    
    # Keep other metrics
    profile["impulsiveness"] = round(avg_impulsive, 3)
    profile["sunk_cost"] = round(avg_sunk_cost, 3)
    profile["confirmation_bias"] = round(avg_confirmation_bias, 3)
    profile["overconfidence"] = round(avg_overconfidence, 3)
    
    update_twin_state(db, user_id, "decision_profile", profile)
    
    explanation = {
        "evidence": f"Logged choice variables across {n_steps} steps. Average decision speed: {round(log.decision_speed_seconds / n_steps, 1)}s per choice.",
        "reasoning": f"Identified {len(biases_detected)} active cognitive bias flags. Blended metrics into overall Digital Twin profile with alpha = 0.3.",
        "confidence": 0.9
    }
    
    return {
        "score": decision_score,
        "feedback": feedback_intro,
        "metrics": metrics,
        "biases_detected": biases_detected,
        "explanation": explanation
    }
