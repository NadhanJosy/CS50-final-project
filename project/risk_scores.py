"""
risk_scores.py - Clinical Risk Scoring Systems (qSOFA, NIHSS, etc.)

AI Assistance Disclosure:
This project was started during Week 6 of CS50 and developed over approximately
two months. I used AI tools (Claude / Gemini) as a support resource during
development.

PROJECT OWNERSHIP:
- I designed the overall structure of the project
- I chose which features to build and how they should behave
- I made the key technical decisions throughout development

HOW AI WAS USED:
- Helping troubleshoot errors and unexpected behaviour
- Assisting when I was stuck on specific problems
- Providing examples or suggestions that I then worked from

All code included in this repository was either written by me or reviewed,
adapted, and implemented by me as part of the final system.

"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level categorization"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"



@dataclass
class ScoreResult:
    """Generic score result"""
    score: int
    max_score: int
    risk_level: RiskLevel
    interpretation: str
    recommendations: List[str] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)
    score_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': self.score,
            'max_score': self.max_score,
            'risk_level': self.risk_level.value,
            'interpretation': self.interpretation,
            'recommendations': self.recommendations,
            'missing_data': self.missing_data,
            'score_details': self.score_details
        }




class RiskScoreCalculator:

    def __init__(self):
        logger.info("Initializing Risk Score Calculator")
        self.scores_calculated = {}

    def calculate_qsofa(
        self,
        systolic_bp: Optional[int] = None,
        respiratory_rate: Optional[int] = None,
        gcs_score: Optional[int] = None
    ) -> ScoreResult:

        score = 0
        missing = []
        details = {}

        # Respiratory rate criterion
        if respiratory_rate is not None:
            if respiratory_rate >= 22:
                score += 1
                details['respiratory_rate'] = f"{respiratory_rate} ≥22 (+1)"
            else:
                details['respiratory_rate'] = f"{respiratory_rate} <22 (0)"
        else:
            missing.append('respiratory_rate')

        # Altered mentation criterion
        if gcs_score is not None:
            if gcs_score < 15:
                score += 1
                details['mentation'] = f"GCS {gcs_score} <15 (+1)"
            else:
                details['mentation'] = f"GCS {gcs_score} =15 (0)"
        else:
            missing.append('gcs_score')

        # Systolic BP criterion
        if systolic_bp is not None:
            if systolic_bp <= 100:
                score += 1
                details['systolic_bp'] = f"{systolic_bp} ≤100 (+1)"
            else:
                details['systolic_bp'] = f"{systolic_bp} >100 (0)"
        else:
            missing.append('systolic_bp')

        # Determine risk level
        if score >= 2:
            risk_level = RiskLevel.HIGH
            interpretation = "High risk for poor outcomes. Sepsis workup indicated."
        elif score == 1:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate risk. Consider sepsis evaluation."
        else:
            risk_level = RiskLevel.LOW
            interpretation = "Low risk for sepsis-related adverse outcomes."

        # Generate recommendations
        recommendations = []
        if score >= 2:
            recommendations.extend([
                "🚨 qSOFA ≥2: High risk for sepsis",
                "Obtain blood cultures before antibiotics",
                "Start broad-spectrum antibiotics within 1 hour",
                "Measure lactate level",
                "Consider ICU consultation"
            ])
        elif score == 1:
            recommendations.extend([
                "Monitor closely for sepsis progression",
                "Reassess qSOFA with each vital signs check",
                "Consider infection workup"
            ])

        if missing:
            recommendations.append(
                f"ℹ️ Incomplete data ({', '.join(missing)}) - obtain for accurate assessment"
            )

        logger.info(f"qSOFA calculated: {score}/3 ({risk_level.value})")

        return ScoreResult(
            score=score,
            max_score=3,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            missing_data=missing,
            score_details=details
        )

    def calculate_nihss(
        self,
        # Level of consciousness
        loc_questions: Optional[int] = None,  # 0-2
        loc_commands: Optional[int] = None,   # 0-2
        gaze: Optional[int] = None,           # 0-2
        visual_fields: Optional[int] = None,  # 0-3
        facial_palsy: Optional[int] = None,   # 0-3
        # Motor function
        motor_left_arm: Optional[int] = None,   # 0-4
        motor_right_arm: Optional[int] = None,  # 0-4
        motor_left_leg: Optional[int] = None,   # 0-4
        motor_right_leg: Optional[int] = None,  # 0-4
        # Other
        ataxia: Optional[int] = None,          # 0-2
        sensory: Optional[int] = None,         # 0-2
        language: Optional[int] = None,        # 0-3
        dysarthria: Optional[int] = None,      # 0-2
        extinction: Optional[int] = None       # 0-2
    ) -> ScoreResult:

        components = {
            'LOC Questions': loc_questions,
            'LOC Commands': loc_commands,
            'Gaze': gaze,
            'Visual Fields': visual_fields,
            'Facial Palsy': facial_palsy,
            'Motor Left Arm': motor_left_arm,
            'Motor Right Arm': motor_right_arm,
            'Motor Left Leg': motor_left_leg,
            'Motor Right Leg': motor_right_leg,
            'Ataxia': ataxia,
            'Sensory': sensory,
            'Language': language,
            'Dysarthria': dysarthria,
            'Extinction/Inattention': extinction
        }

        score = 0
        missing = []
        details = {}

        for name, value in components.items():
            if value is not None:
                score += value
                details[name] = value
            else:
                missing.append(name)

        # Determine risk level and interpretation
        if score == 0:
            risk_level = RiskLevel.MINIMAL
            interpretation = "No stroke symptoms detected"
        elif score <= 4:
            risk_level = RiskLevel.LOW
            interpretation = "Minor stroke"
        elif score <= 15:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate stroke"
        elif score <= 20:
            risk_level = RiskLevel.HIGH
            interpretation = "Moderate to severe stroke"
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "Severe stroke"

        # Generate recommendations
        recommendations = []
        if score > 0:
            recommendations.append("🚨 Stroke detected - activate stroke protocol")
            recommendations.append("CT head STAT (rule out hemorrhage)")
            recommendations.append("Check time of symptom onset (thrombolysis window)")

            if score >= 16:
                recommendations.append("Consider thrombectomy evaluation")
                recommendations.append("Neurology/stroke team consultation STAT")

            if score <= 4:
                recommendations.append("May be candidate for outpatient management if stable")

        if missing:
            recommendations.append(
                f"ℹ️ Incomplete NIHSS ({len(missing)} items missing) - "
                "complete exam for accurate score"
            )

        logger.info(f"NIHSS calculated: {score}/42 ({interpretation})")

        return ScoreResult(
            score=score,
            max_score=42,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            missing_data=missing,
            score_details=details
        )

    def calculate_cha2ds2vasc(
        self,
        age: Optional[int] = None,
        sex: Optional[str] = None,  # 'M' or 'F'
        has_chf: bool = False,
        has_hypertension: bool = False,
        has_diabetes: bool = False,
        has_stroke_tia: bool = False,
        has_vascular_disease: bool = False
    ) -> ScoreResult:

        score = 0
        missing = []
        details = {}

        # CHF
        if has_chf:
            score += 1
            details['CHF'] = "+1"

        # Hypertension
        if has_hypertension:
            score += 1
            details['Hypertension'] = "+1"

        # Age
        if age is not None:
            if age >= 75:
                score += 2
                details['Age'] = f"{age} years (+2)"
            elif age >= 65:
                score += 1
                details['Age'] = f"{age} years (+1)"
            else:
                details['Age'] = f"{age} years (0)"
        else:
            missing.append('age')

        # Diabetes
        if has_diabetes:
            score += 1
            details['Diabetes'] = "+1"

        # Stroke/TIA
        if has_stroke_tia:
            score += 2
            details['Stroke/TIA'] = "+2"

        # Vascular disease
        if has_vascular_disease:
            score += 1
            details['Vascular Disease'] = "+1"

        # Sex
        if sex:
            if sex.upper() == 'F':
                score += 1
                details['Sex'] = "Female (+1)"
            else:
                details['Sex'] = "Male (0)"
        else:
            missing.append('sex')

        # Determine risk level
        if score == 0:
            risk_level = RiskLevel.LOW
            interpretation = "Low risk (0.2% annual stroke risk)"
        elif score == 1:
            risk_level = RiskLevel.LOW
            interpretation = "Low-moderate risk (0.6% annual stroke risk)"
        elif score <= 3:
            risk_level = RiskLevel.MODERATE
            interpretation = f"Moderate risk ({['2.2%', '2.2%', '3.2%'][score-2]} annual stroke risk)"
        elif score <= 5:
            risk_level = RiskLevel.HIGH
            interpretation = f"High risk ({['4.8%', '7.2%'][score-4]} annual stroke risk)"
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = f"Very high risk (>9% annual stroke risk)"

        # Recommendations
        recommendations = []
        if score >= 2:
            recommendations.append(
                "🩸 Anticoagulation recommended (unless contraindicated)"
            )
            recommendations.append(
                "Options: Warfarin (INR 2-3) or DOAC (apixaban, rivaroxaban, etc.)"
            )
        elif score == 1:
            if sex and sex.upper() == 'F' and score == 1:
                recommendations.append(
                    "Consider anticoagulation vs. aspirin (shared decision making)"
                )
            else:
                recommendations.append(
                    "Anticoagulation recommended for most patients"
                )
        else:
            recommendations.append(
                "Low risk - anticoagulation generally not recommended"
            )

        recommendations.append(
            "Reassess score annually and with status changes"
        )

        if missing:
            recommendations.append(
                f"ℹ️ Missing data: {', '.join(missing)}"
            )

        logger.info(f"CHA₂DS₂-VASc calculated: {score}/9 ({risk_level.value})")

        return ScoreResult(
            score=score,
            max_score=9,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            missing_data=missing,
            score_details=details
        )

    def calculate_curb65(
        self,
        confusion: bool = False,
        urea_mmol_l: Optional[float] = None,
        respiratory_rate: Optional[int] = None,
        systolic_bp: Optional[int] = None,
        diastolic_bp: Optional[int] = None,
        age: Optional[int] = None
    ) -> ScoreResult:

        score = 0
        missing = []
        details = {}

        # Confusion
        if confusion:
            score += 1
            details['Confusion'] = "Present (+1)"
        else:
            details['Confusion'] = "Absent (0)"

        # Urea
        if urea_mmol_l is not None:
            if urea_mmol_l > 7:
                score += 1
                details['Urea'] = f"{urea_mmol_l} mmol/L >7 (+1)"
            else:
                details['Urea'] = f"{urea_mmol_l} mmol/L ≤7 (0)"
        else:
            missing.append('urea')

        # Respiratory rate
        if respiratory_rate is not None:
            if respiratory_rate >= 30:
                score += 1
                details['Respiratory Rate'] = f"{respiratory_rate} ≥30 (+1)"
            else:
                details['Respiratory Rate'] = f"{respiratory_rate} <30 (0)"
        else:
            missing.append('respiratory_rate')

        # Blood pressure
        if systolic_bp is not None and diastolic_bp is not None:
            if systolic_bp < 90 or diastolic_bp <= 60:
                score += 1
                details['Blood Pressure'] = f"{systolic_bp}/{diastolic_bp} (+1)"
            else:
                details['Blood Pressure'] = f"{systolic_bp}/{diastolic_bp} (0)"
        else:
            missing.append('blood_pressure')

        # Age
        if age is not None:
            if age >= 65:
                score += 1
                details['Age'] = f"{age} years ≥65 (+1)"
            else:
                details['Age'] = f"{age} years <65 (0)"
        else:
            missing.append('age')

        # Determine risk level
        if score <= 1:
            risk_level = RiskLevel.LOW
            interpretation = "Low severity - suitable for outpatient treatment"
        elif score == 2:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate severity - consider hospitalization"
        else:
            risk_level = RiskLevel.HIGH
            interpretation = f"High severity (score {score}) - hospitalize, consider ICU"

        # Recommendations
        recommendations = []
        if score <= 1:
            recommendations.append(
                "✓ Low risk - outpatient treatment appropriate"
            )
            recommendations.append(
                "Oral antibiotics (e.g., amoxicillin, doxycycline, or macrolide)"
            )
            recommendations.append(
                "Close follow-up in 48-72 hours"
            )
        elif score == 2:
            recommendations.append(
                "⚠️ Moderate risk - hospitalization vs. close outpatient monitoring"
            )
            recommendations.append(
                "Consider additional risk factors and social circumstances"
            )
        else:
            recommendations.append(
                "🚨 High risk - hospitalize immediately"
            )
            recommendations.append(
                "IV antibiotics (e.g., ceftriaxone + azithromycin)"
            )
            recommendations.append(
                "Chest X-ray, blood cultures, CBC, BMP"
            )
            if score >= 4:
                recommendations.append(
                    "Consider ICU admission"
                )

        if missing:
            recommendations.append(
                f"ℹ️ Missing: {', '.join(missing)} - obtain for complete score"
            )

        logger.info(f"CURB-65 calculated: {score}/5 ({risk_level.value})")

        return ScoreResult(
            score=score,
            max_score=5,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            missing_data=missing,
            score_details=details
        )

    def calculate_meld(
        self,
        creatinine_mg_dl: Optional[float] = None,
        bilirubin_mg_dl: Optional[float] = None,
        inr: Optional[float] = None,
        dialysis_twice: bool = False
    ) -> ScoreResult:

        import math

        missing = []

        if creatinine_mg_dl is None:
            missing.append('creatinine')
        if bilirubin_mg_dl is None:
            missing.append('bilirubin')
        if inr is None:
            missing.append('INR')

        if missing:
            return ScoreResult(
                score=0,
                max_score=40,
                risk_level=RiskLevel.LOW,
                interpretation="Cannot calculate - missing required lab values",
                recommendations=[
                    f"ℹ️ Obtain: {', '.join(missing)}"
                ],
                missing_data=missing
            )

        # Apply floor values
        creat = max(1.0, creatinine_mg_dl)
        bili = max(1.0, bilirubin_mg_dl)
        inr_val = max(1.0, inr)

        # If on dialysis twice in past week, use creatinine = 4.0
        if dialysis_twice:
            creat = 4.0

        # Calculate MELD score
        try:
            raw_score = (
                10 * (
                    0.957 * math.log(creat) +
                    0.378 * math.log(bili) +
                    1.120 * math.log(inr_val) +
                    0.643
                )
            )

            # Round and cap
            score = max(6, min(40, round(raw_score)))

        except (ValueError, OverflowError) as e:
            logger.error(f"MELD calculation error: {e}")
            return ScoreResult(
                score=0,
                max_score=40,
                risk_level=RiskLevel.LOW,
                interpretation="Calculation error - check lab values",
                recommendations=["⚠️ Invalid lab values for MELD calculation"],
                missing_data=[]
            )

        # Determine risk level
        if score < 10:
            risk_level = RiskLevel.LOW
            interpretation = f"MELD {score}: 1.9% 90-day mortality"
        elif score < 20:
            risk_level = RiskLevel.MODERATE
            interpretation = f"MELD {score}: ~6% 90-day mortality"
        elif score < 30:
            risk_level = RiskLevel.HIGH
            interpretation = f"MELD {score}: ~20% 90-day mortality"
        elif score < 40:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = f"MELD {score}: ~53% 90-day mortality"
        else:
            risk_level = RiskLevel.CRITICAL
            interpretation = f"MELD {score}: >70% 90-day mortality"

        # Recommendations
        recommendations = []
        if score >= 15:
            recommendations.append(
                "⚠️ High MELD score - transplant evaluation indicated"
            )
            recommendations.append(
                "Hepatology/transplant surgery consultation"
            )

        if score >= 30:
            recommendations.append(
                "🚨 Critical MELD score - urgent transplant consideration"
            )
            recommendations.append(
                "ICU-level monitoring may be required"
            )

        recommendations.append(
            "Recalculate MELD regularly (weekly-monthly depending on score)"
        )

        details = {
            'Creatinine': f"{creatinine_mg_dl} mg/dL",
            'Bilirubin': f"{bilirubin_mg_dl} mg/dL",
            'INR': f"{inr}",
            'Dialysis': "Yes (creatinine set to 4.0)" if dialysis_twice else "No"
        }

        logger.info(f"MELD calculated: {score} ({risk_level.value})")

        return ScoreResult(
            score=score,
            max_score=40,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            missing_data=[],
            score_details=details
        )

    def calculate_gcs(
        self,
        eye_opening: Optional[int] = None,     # 1-4
        verbal_response: Optional[int] = None,  # 1-5
        motor_response: Optional[int] = None    # 1-6
    ) -> ScoreResult:

        missing = []
        score = 0

        if eye_opening is not None:
            score += eye_opening
        else:
            missing.append('eye_opening')

        if verbal_response is not None:
            score += verbal_response
        else:
            missing.append('verbal_response')

        if motor_response is not None:
            score += motor_response
        else:
            missing.append('motor_response')

        if missing:
            return ScoreResult(
                score=0,
                max_score=15,
                risk_level=RiskLevel.LOW,
                interpretation="Incomplete GCS assessment",
                recommendations=[f"ℹ️ Assess: {', '.join(missing)}"],
                missing_data=missing
            )

        # Determine risk level
        if score >= 13:
            risk_level = RiskLevel.LOW
            interpretation = f"GCS {score}: Mild impairment"
        elif score >= 9:
            risk_level = RiskLevel.MODERATE
            interpretation = f"GCS {score}: Moderate impairment"
        else:
            risk_level = RiskLevel.CRITICAL
            interpretation = f"GCS {score}: Severe impairment"

        # Recommendations
        recommendations = []
        if score <= 8:
            recommendations.append(
                "🚨 GCS ≤8: Consider airway protection (intubation)"
            )
            recommendations.append(
                "CT head STAT"
            )
            recommendations.append(
                "Neurosurgery/neurology consultation"
            )
            recommendations.append(
                "ICU admission"
            )
        elif score <= 12:
            recommendations.append(
                "⚠️ Moderate impairment - close monitoring required"
            )
            recommendations.append(
                "Frequent neuro checks (q1-2h)"
            )

        details = {
            'Eye Opening': f"{eye_opening}/4",
            'Verbal Response': f"{verbal_response}/5",
            'Motor Response': f"{motor_response}/6"
        }

        logger.info(f"GCS calculated: {score}/15 ({interpretation})")

        return ScoreResult(
            score=score,
            max_score=15,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            missing_data=[],
            score_details=details
        )



__all__ = [
    'RiskScoreCalculator',
    'ScoreResult',
    'RiskLevel',
]
