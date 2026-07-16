-- Hospital Management System: Analytics & Decision Support Queries
-- This file contains over 20 analytical queries structured for a healthcare operations dashboard,
-- demonstrating advanced SQL including CTEs, Window Functions, Joins, Aggregations, and Date Functions.

-- ==========================================
-- SECTION 1: DOCTOR & DEPARTMENT UTILIZATION
-- ==========================================

-- 1. Doctor Utilization (Booked vs Completed)
SELECT
    doctor_id,
    COUNT(*) AS booked_slots,
    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_visits,
    ROUND(100.0 * SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS completion_rate
FROM appointments
GROUP BY doctor_id;

-- 2. Department Capacity vs Demand
SELECT 
    d.name AS department_name,
    COUNT(t.id) AS total_capacity,
    SUM(CASE WHEN t.is_booked = 1 THEN 1 ELSE 0 END) AS total_demand,
    ROUND(100.0 * SUM(CASE WHEN t.is_booked = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(t.id), 0), 2) AS utilization_percentage
FROM departments d
JOIN doctor_profiles dp ON d.id = dp.department_id
JOIN time_slots t ON dp.id = t.doctor_id
GROUP BY d.name
ORDER BY utilization_percentage DESC;

-- 3. Doctor Ranking Within Each Department (By Completed Appointments)
WITH doctor_metrics AS (
    SELECT
        dp.department_id,
        a.doctor_id,
        COUNT(a.id) AS completed_appointments
    FROM appointments a
    JOIN doctor_profiles dp ON a.doctor_id = dp.id
    WHERE a.status = 'COMPLETED'
    GROUP BY dp.department_id, a.doctor_id
)
SELECT
    department_id,
    doctor_id,
    completed_appointments,
    DENSE_RANK() OVER (
        PARTITION BY department_id
        ORDER BY completed_appointments DESC
    ) AS department_rank
FROM doctor_metrics;

-- 4. Underutilized Doctors (Candidates for schedule optimization)
SELECT 
    doctor_id,
    COUNT(*) AS total_slots,
    SUM(CASE WHEN is_booked = 0 THEN 1 ELSE 0 END) AS unbooked_slots,
    ROUND(100.0 * SUM(CASE WHEN is_booked = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS idle_rate
FROM time_slots
GROUP BY doctor_id
HAVING idle_rate > 30.0;

-- 5. Peak Hour Demand (To assist staffing decisions)
SELECT 
    strftime('%H', t.start_time) AS hour_of_day,
    COUNT(a.id) AS appointment_volume
FROM appointments a
JOIN time_slots t ON a.slot_id = t.id
GROUP BY hour_of_day
ORDER BY appointment_volume DESC;


-- ==========================================
-- SECTION 2: PATIENT BEHAVIOR & NO-SHOWS
-- ==========================================

-- 6. Department-wise No-Show Rate
SELECT
    dp.department_id,
    COUNT(a.id) AS total_appointments,
    SUM(CASE WHEN a.status = 'NO_SHOW' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'NO_SHOW' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 2) AS no_show_rate
FROM appointments a
JOIN doctor_profiles dp ON a.doctor_id = dp.id
GROUP BY dp.department_id;

-- 7. High No-Show Risk Segments (By Day of Week)
SELECT 
    strftime('%w', t.start_time) AS day_of_week,
    COUNT(a.id) AS total_appointments,
    SUM(CASE WHEN a.status = 'NO_SHOW' THEN 1 ELSE 0 END) AS no_shows,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'NO_SHOW' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 2) AS no_show_rate
FROM appointments a
JOIN time_slots t ON a.slot_id = t.id
GROUP BY day_of_week
ORDER BY no_show_rate DESC;

-- 8. Patient Revisit Frequency (New vs Returning)
WITH patient_visits AS (
    SELECT 
        patient_id,
        COUNT(*) AS total_visits
    FROM appointments
    WHERE status = 'COMPLETED'
    GROUP BY patient_id
)
SELECT 
    CASE 
        WHEN total_visits = 1 THEN 'New Patient (1 Visit)'
        WHEN total_visits BETWEEN 2 AND 5 THEN 'Returning (2-5 Visits)'
        ELSE 'Frequent (>5 Visits)'
    END AS patient_segment,
    COUNT(*) AS patient_count
FROM patient_visits
GROUP BY patient_segment;

-- 9. Repeat No-Show Offenders
SELECT 
    patient_id,
    COUNT(id) AS missed_appointments
FROM appointments
WHERE status = 'NO_SHOW'
GROUP BY patient_id
HAVING missed_appointments > 1
ORDER BY missed_appointments DESC;

-- 10. Cancellation Reasons Breakdown
SELECT 
    cancel_reason,
    COUNT(id) AS cancellation_count
FROM appointments
WHERE status = 'CANCELLED' AND cancel_reason IS NOT NULL
GROUP BY cancel_reason
ORDER BY cancellation_count DESC;


-- ==========================================
-- SECTION 3: WAIT TIMES & EFFICIENCY
-- ==========================================

-- 11. Average Patient Wait Time (Checked In to Started)
SELECT 
    dp.department_id,
    AVG(
        (julianday(a.started_at) - julianday(a.checked_in_at)) * 24 * 60
    ) AS avg_wait_time_minutes
FROM appointments a
JOIN doctor_profiles dp ON a.doctor_id = dp.id
WHERE a.started_at IS NOT NULL AND a.checked_in_at IS NOT NULL
GROUP BY dp.department_id;

-- 12. Appointment Lead Time (Booked to Confirmed/Scheduled Time)
SELECT 
    dp.department_id,
    AVG(
        (julianday(t.start_time) - julianday(a.booked_at)) * 24
    ) AS avg_lead_time_hours
FROM appointments a
JOIN time_slots t ON a.slot_id = t.id
JOIN doctor_profiles dp ON a.doctor_id = dp.id
WHERE a.booked_at IS NOT NULL
GROUP BY dp.department_id;

-- 13. Average Consultation Duration
SELECT 
    doctor_id,
    AVG(
        (julianday(completed_at) - julianday(started_at)) * 24 * 60
    ) AS avg_consultation_minutes
FROM appointments
WHERE status = 'COMPLETED' AND started_at IS NOT NULL AND completed_at IS NOT NULL
GROUP BY doctor_id;

-- 14. Departments with Consistently High Wait Times (Bottleneck Identification)
SELECT 
    dp.department_id,
    AVG((julianday(a.started_at) - julianday(a.checked_in_at)) * 24 * 60) AS avg_wait_time
FROM appointments a
JOIN doctor_profiles dp ON a.doctor_id = dp.id
WHERE a.started_at IS NOT NULL AND a.checked_in_at IS NOT NULL
GROUP BY dp.department_id
HAVING avg_wait_time > 30.0; -- Threshold of 30 minutes


-- ==========================================
-- SECTION 4: TIME-SERIES & TRENDS
-- ==========================================

-- 15. 7-Day Rolling Average of Appointments (Trend Analysis)
WITH daily_counts AS (
    SELECT 
        DATE(booked_at) AS booking_date,
        COUNT(*) AS daily_appointments
    FROM appointments
    GROUP BY DATE(booked_at)
)
SELECT 
    booking_date,
    daily_appointments,
    AVG(daily_appointments) OVER (
        ORDER BY booking_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7d_avg
FROM daily_counts;

-- 16. Month-Over-Month Appointment Volume Growth
WITH monthly_volume AS (
    SELECT 
        strftime('%Y-%m', booked_at) AS month,
        COUNT(id) AS volume
    FROM appointments
    GROUP BY strftime('%Y-%m', booked_at)
)
SELECT 
    month,
    volume,
    LAG(volume) OVER (ORDER BY month) AS prev_month_volume,
    ROUND(100.0 * (volume - LAG(volume) OVER (ORDER BY month)) / NULLIF(LAG(volume) OVER (ORDER BY month), 0), 2) AS mom_growth_pct
FROM monthly_volume;


-- ==========================================
-- SECTION 5: OPERATIONAL RECOMMENDATIONS
-- ==========================================

-- 17. Identify days/time slots requiring additional staffing
-- Finds days where total booked appointments exceed 85% of total department capacity
WITH daily_capacity AS (
    SELECT 
        DATE(t.start_time) AS schedule_date,
        dp.department_id,
        COUNT(t.id) AS total_slots,
        SUM(CASE WHEN t.is_booked = 1 THEN 1 ELSE 0 END) AS booked_slots
    FROM time_slots t
    JOIN doctor_profiles dp ON t.doctor_id = dp.id
    GROUP BY schedule_date, dp.department_id
)
SELECT 
    schedule_date,
    department_id,
    total_slots,
    booked_slots,
    ROUND(100.0 * booked_slots / total_slots, 2) AS utilization_pct,
    'High Demand - Recommend adding more slots or on-call staff' AS recommendation
FROM daily_capacity
WHERE (1.0 * booked_slots / total_slots) > 0.85;

-- 18. Patients who need a proactive reminder (High no-show probability heuristic)
-- Finds patients with previous no-shows who have an upcoming appointment in the next 48 hours
SELECT 
    a.patient_id,
    a.id AS upcoming_appointment_id,
    t.start_time
FROM appointments a
JOIN time_slots t ON a.slot_id = t.id
WHERE a.status = 'CONFIRMED'
  AND t.start_time BETWEEN datetime('now') AND datetime('now', '+2 days')
  AND a.patient_id IN (
      SELECT patient_id FROM appointments WHERE status = 'NO_SHOW'
  );

-- 19. View: Executive Dashboard View
-- Consolidates key daily KPIs into a single view for BI tools
CREATE VIEW IF NOT EXISTS vw_executive_dashboard AS
SELECT 
    DATE(a.booked_at) AS report_date,
    COUNT(a.id) AS total_bookings,
    SUM(CASE WHEN a.status = 'COMPLETED' THEN 1 ELSE 0 END) AS total_completed,
    SUM(CASE WHEN a.status = 'NO_SHOW' THEN 1 ELSE 0 END) AS total_no_shows,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'COMPLETED' THEN 1 ELSE 0 END) / COUNT(a.id), 2) AS completion_rate,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'NO_SHOW' THEN 1 ELSE 0 END) / COUNT(a.id), 2) AS no_show_rate
FROM appointments a
GROUP BY DATE(a.booked_at);

-- 20. Indexing Recommendations for Analytics Queries
-- Creating indexes to optimize the analytical queries above
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_time_slots_start ON time_slots(start_time);
CREATE INDEX IF NOT EXISTS idx_time_slots_booked ON time_slots(is_booked);
