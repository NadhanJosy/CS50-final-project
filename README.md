# Clinical Decision Support System (CDSS) - CS50 Final Project

## Video Demo

[https://youtu.be/aMV3yRrnPf4](https://youtu.be/aMV3yRrnPf4)

### Project Overview

For my CS50 final project, I built a Clinical Decision Support System (CDSS) - a web-based diagnostic tool designed to assist
healthcare professionals in making clinical decisions. The system analyzes patient symptoms and provides a ranked list of potential
diagnoses with confidence levels, along with clinical recommendations and risk assessments. This project combines my interests in
healthcare and computer science, and while it's designed as an educational tool, it follows real-world medical decision-making
principles.

The inspiration came from wanting to create something that could have genuine real-world impact. Medical diagnosis is complex and
error-prone, and clinical decision support tools are increasingly used in hospitals to reduce diagnostic errors and improve patient
outcomes. I wanted to build something that felt professional and could demonstrate enterprise-level software engineering practices.

Technical Architecture

Core Technologies

Backend: Python 3 with Flask web framework
Database: SQLite with CS50's SQL library
Frontend: Bootstrap 5 for responsive design, vanilla JavaScript for interactivity
Authentication: Werkzeug for password hashing with session-based auth

Design Philosophy

I made several key architectural decisions that shaped the project:

Hybrid Diagnostic Engine: Rather than using pure keyword matching, I implemented a hybrid system combining Bayesian inference
(probability-based reasoning) with rule-based pattern matching. This was crucial because I discovered early on that simple keyword
matching missed critical conditions like meningitis and appendicitis that have specific symptom combinations. The pattern-matching
layer catches these "textbook presentations" that Bayesian alone might miss.

Graceful Degradation: The system is designed to work even if enhanced modules aren't available. The main app.py can fall back to
basic functionality if optional components like vital signs analysis or risk scoring aren't installed. This makes the project more
maintainable and easier to deploy.
Defensive Programming: Every function includes comprehensive error handling, type hints, and input validation. I chose this approach
because in healthcare software, failures can be critical. The system logs errors, provides fallbacks, and never crashes - it always
gives the user actionable information.

File Structure and Functionality

app.py (Main Application)
This is the heart of the system. It handles all HTTP routing, user authentication, and API endpoints. I structured it to separate
concerns: authentication routes at the top, diagnostic API in the middle, and administrative functions at the bottom.

Key design choice: I used decorators (@login_required, @admin_required) for route protection rather than checking authentication in
every function. This keeps the code DRY and makes security easier to maintain.

The /api/diagnose endpoint accepts symptom descriptions and optional vital signs data, processes them through the diagnostic engine,
and returns a comprehensive JSON response. I chose JSON for API responses because it's structured, easy to parse in JavaScript, and
follows modern API design principles.

engine.py (Diagnostic Engine)

This file contains the core diagnostic logic. The DiagnosticEngine class loads a trained model (disease-symptom probability data) and
performs Bayesian inference to calculate disease probabilities.

Major design decision: I implemented a two-stage diagnosis process:

Stage 1: Pure Bayesian calculation using P(disease|symptoms)
Stage 2: Pattern-based boosting for critical conditions

Why? Because Bayesian inference alone doesn't account for symptom combinations that are pathognomonic (diagnostic) for specific
diseases. For example, "right lower quadrant pain + migrating from periumbilical area + fever" is classic appendicitis, but Bayesian
might not weight this combination heavily enough without the pattern matcher.

The engine returns a DiagnosticResult dataclass (I used dataclasses for type safety and clean serialization) containing the
differential diagnosis, confidence scores, urgency flags, and clinical recommendations.

helpers.py (Utility Functions)

This contains all the helper functions for authentication, input sanitization, logging, and data formatting. I extracted these into a
separate file following the Single Responsibility Principle - each function does one thing well.

Notable functions:

sanitize_input(): Strips dangerous HTML/JavaScript to prevent XSS attacks
log_audit(): Records all user actions for compliance and debugging
calculate_confidence(): Determines confidence levels based on probability gaps and symptom count

I made logging comprehensive because in a real clinical system, you need a complete audit trail for liability and quality improvement.
enhanced_mappings.py (Medical Terminology)
This was one of the most challenging parts. Medical professionals use many different terms for the same symptom - "dyspnea,"
"shortness of breath," "SOB," "difficulty breathing" all mean the same thing. I researched medical terminology and compiled 200+
synonym mappings.

I also added anatomical location detection (RLQ, LUQ, epigastric, etc.) because location is critical for diagnosis. "Right lower
quadrant pain" strongly suggests appendicitis, but "epigastric pain" suggests gastric issues. The pattern matching system uses these
locations as additional evidence.

Design trade-off: I chose to map multiple terms to canonical symptom names rather than trying to understand natural language. This is
less flexible than NLP but more reliable and faster.

Database (schema.sql, init_db.py)

The database schema supports user management, consultation records, audit logging, and system metrics. I chose SQLite for simplicity
and portability, though the schema is designed to be easily migrated to PostgreSQL for production use.

Key tables:

users: Authentication and profiles
consultations: Complete diagnostic records with JSON fields for flexibility
audit_log: Every system action logged with timestamp, user, and details
disclaimer_acceptances: Legal compliance tracking

Design choice: I store the full diagnostic response as JSON in the response column rather than normalizing everything into separate
tables. This trades some storage efficiency for query simplicity and preserves the complete diagnostic context.

Templates and Static Files

The frontend uses Bootstrap 5 for responsive design. I chose a medical professional aesthetic - clean, minimal, with clear
information hierarchy. The chat interface mimics modern AI chat apps for familiarity.
The JavaScript is vanilla (no frameworks) because the interactivity needs are simple and I wanted to minimize dependencies. The chat
interface updates dynamically, formats differential diagnoses with progress bars, and highlights critical warnings in red.

Challenges and Solutions

Challenge 1: Missing Critical Diagnoses
Initial testing showed the system missed meningitis and appendicitis cases. I analyzed why and realized these conditions have
specific symptom combinations that pure Bayesian inference doesn't capture well. Solution: Added pattern-based boosting for critical
conditions.

Challenge 2: Medical Terminology Variations
Doctors use many terms for the same symptom. Solution: Built comprehensive synonym mappings through medical literature research and
medical terminology databases.

Challenge 3: Balancing Accuracy and Safety
Should the system prioritize sensitivity (catch all critical cases, more false positives) or specificity (fewer false positives,
might miss cases)? I chose sensitivity for critical conditions because in medicine, missing a life-threatening diagnosis is worse
than overcalling.

Challenge 4: User Experience
Medical software is often clunky. I focused on making the interface simple: type symptoms, get immediate results with clear visual
hierarchy. Critical warnings appear first in red, recommendations are actionable.

Future Enhancements
If I continue this project, I would add:

Lab Results Integration: Upload CBC, metabolic panels, and have the system factor lab values into diagnoses
Drug Interaction Checker: Alert for dangerous drug combinations
Imaging Guidelines: Recommend appropriate imaging studies (CT, MRI, X-ray) based on suspected diagnosis
Multi-language Support: Spanish and other languages for broader accessibility

Conclusion

This project taught me how to build enterprise-grade software with proper error handling, security practices, and user-centered
design. It combines multiple CS concepts: web development, databases, algorithms (Bayesian inference), data structures, and API
design. Most importantly, it solves a real problem - helping healthcare providers make better diagnostic decisions.

While this is an educational tool, not approved for clinical use, I'm proud that the architecture and code quality could serve as a
foundation for a real clinical decision support system. Every design decision was made with real-world deployment in mind:
comprehensive error handling, audit logging, security measures, and defensive programming throughout.

AI Assistance Disclosure

This project was started during Week 6 of CS50 and developed over approximately two months. I used AI tools (Claude and Gemini) as
support resources during development.

PROJECT OWNERSHIP:

I designed the overall structure of the project
I chose which features to build and how they should behave
I made all key technical decisions throughout development
I tested and debugged the system to ensure it met my specifications

HOW AI WAS USED:

Helping troubleshoot errors and unexpected behaviour
Assisting when I was stuck on specific problems
Providing examples or suggestions that I then adapted and implemented
Compiling medical terminology data from published sources

All code included in this repository was either written by me or reviewed, adapted, and implemented by me as part of the final
system. I understand every component and can explain its functionality.
