import { PrismaClient } from "@prisma/client";
import { clinicalRules } from "../lib/clinical-safety";
import { patients } from "../lib/seed-data";

const prisma = new PrismaClient();

async function main() {
  await prisma.auditLog.deleteMany();
  await prisma.clinicalRule.deleteMany();
  await prisma.qualityMetric.deleteMany();
  await prisma.patient.deleteMany();
  await prisma.userRole.deleteMany();
  await prisma.user.deleteMany();
  await prisma.role.deleteMany();

  const roles = [
    ["SUPER_ADMIN", "Cau hinh he thong va audit"],
    ["PHYSICIAN", "Bac si phu trach lam sang"],
    ["NURSE_COORDINATOR", "Dieu duong va care coordinator"],
    ["RECEPTIONIST", "Le tan va hanh chinh"],
    ["PHARMACIST", "Duoc si cong tac"],
    ["QUALITY_MANAGER", "Quan ly chat luong"],
    ["PATIENT", "Nguoi benh"]
  ] as const;

  for (const [name, description] of roles) {
    await prisma.role.create({ data: { name, description } });
  }

  for (const rule of clinicalRules) {
    await prisma.clinicalRule.create({
      data: {
        ruleName: rule.ruleName,
        ruleDescription: rule.ruleDescription,
        severity: rule.severity,
        suggestedAction: rule.suggestedAction,
        requiresPhysicianConfirmation: rule.requiresPhysicianConfirmation,
        version: rule.version,
        effectiveDate: new Date(rule.effectiveDate),
        reviewDate: new Date(rule.reviewDate),
        approvedBy: rule.approvedBy
      }
    });
  }

  for (const patient of patients) {
    await prisma.patient.create({
      data: {
        medicalRecordNumber: patient.medicalRecordNumber,
        fullName: patient.fullName,
        dateOfBirth: new Date(patient.dateOfBirth),
        sex: patient.sex,
        phone: patient.phone,
        address: patient.address,
        emergencyContact: patient.emergencyContact,
        primaryCaregiver: patient.primaryCaregiver,
        occupation: patient.occupation,
        insuranceInformation: patient.insuranceInformation,
        consentStatus: patient.consentStatus,
        consentDate: new Date("2026-06-01"),
        status: patient.status,
        conditions: {
          create: patient.conditions.map((condition) => ({
            conditionCode: condition.conditionCode,
            conditionName: condition.conditionName,
            diagnosedDate: new Date(condition.diagnosedDate),
            status: condition.status,
            severity: condition.severity,
            complications: condition.complications,
            notes: condition.notes,
            createdBy: "seed"
          }))
        },
        medications: {
          create: patient.medications.map((medication) => ({
            drugName: medication.drugName,
            genericName: medication.genericName,
            dose: medication.dose,
            route: medication.route,
            frequency: medication.frequency,
            indication: medication.indication,
            startDate: new Date(medication.startDate),
            prescribingProvider: medication.prescribingProvider,
            adherenceStatus: medication.adherenceStatus,
            allergyOrIntolerance: medication.allergyOrIntolerance,
            isActive: medication.isActive,
            medicationClass: medication.medicationClass,
            category: medication.category,
            lastReconciledAt: new Date("2026-06-18"),
            lastReconciledBy: "seed"
          }))
        },
        vitalSigns: {
          create: patient.vitals.map((vital) => ({
            systolicBp: vital.systolicBp,
            diastolicBp: vital.diastolicBp,
            heartRate: vital.heartRate,
            respiratoryRate: vital.respiratoryRate,
            temperature: vital.temperature,
            spo2: vital.spo2,
            weightKg: vital.weightKg,
            heightCm: vital.heightCm,
            bmi: vital.bmi,
            waistCircumferenceCm: vital.waistCircumferenceCm,
            painScore: vital.painScore,
            measuredBy: "seed",
            measuredAt: new Date(vital.measuredAt)
          }))
        },
        laboratoryResults: {
          create: patient.labs.map((lab) => ({
            testCode: lab.testCode,
            testName: lab.testName,
            resultValue: String(lab.resultValue),
            unit: lab.unit,
            abnormalFlag: lab.abnormalFlag,
            collectedDate: new Date(lab.collectedDate),
            reportedDate: new Date(lab.collectedDate),
            source: "seed",
            reviewStatus: lab.reviewStatus
          }))
        },
        appointments: {
          create: patient.appointments.map((appointment) => ({
            appointmentType: appointment.appointmentType,
            scheduledAt: new Date(appointment.scheduledAt),
            durationMinutes: 30,
            providerId: appointment.providerName,
            status: appointment.status,
            reason: appointment.reason,
            riskFlag: appointment.riskFlag,
            reminderStatus: appointment.reminderStatus
          }))
        },
        carePlans: {
          create: {
            createdBy: "seed",
            approvedBy: patient.carePlan.approvedBy,
            status: patient.carePlan.status,
            riskLevel: patient.carePlan.riskLevel,
            mainProblems: patient.carePlan.mainProblems,
            medicationPlan: patient.carePlan.medicationPlan,
            lifestylePlan: patient.carePlan.lifestylePlan,
            monitoringPlan: patient.carePlan.monitoringPlan,
            laboratoryPlan: patient.carePlan.laboratoryPlan,
            referralPlan: patient.carePlan.referralPlan,
            redFlagPlan: patient.carePlan.redFlagPlan,
            nextFollowUpDate: patient.carePlan.nextFollowUpDate ? new Date(patient.carePlan.nextFollowUpDate) : null,
            goals: {
              create: patient.carePlan.goals.map((goal) => ({
                goalDomain: goal.goalDomain,
                goalName: goal.goalName,
                baselineValue: goal.baselineValue,
                targetValue: goal.targetValue,
                targetUnit: goal.targetUnit,
                targetDate: new Date(goal.targetDate),
                status: goal.status,
                notes: goal.notes
              }))
            }
          }
        },
        tasks: {
          create: patient.tasks.map((task) => ({
            assignedTo: task.assignedTo,
            taskType: task.taskType,
            priority: task.priority,
            status: task.status,
            dueDate: new Date(task.dueDate),
            notes: task.notes,
            createdBy: "seed"
          }))
        },
        referrals: {
          create: patient.referrals.map((referral) => ({
            referralType: referral.referralType,
            destination: referral.destination,
            specialty: referral.specialty,
            reason: referral.reason,
            urgency: referral.urgency,
            status: referral.status,
            createdBy: "seed"
          }))
        }
      }
    });
  }
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });
