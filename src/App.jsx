import React, { useState, useEffect, useMemo } from 'react';
import { ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';

// Simple CSV parser that handles quotes
function parseCSV(text) {
    const lines = text.split(/\r?\n/).filter(line => line.trim());
    if (lines.length === 0) return [];

    const parseLine = (line) => {
        const result = [];
        let cur = '';
        let inQuotes = false;
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            const nextChar = line[i + 1];
            if (char === '"' && inQuotes && nextChar === '"') {
                cur += '"';
                i++;
            } else if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(cur.trim());
                cur = '';
            } else {
                cur += char;
            }
        }
        result.push(cur.trim());
        return result;
    };

    const headers = parseLine(lines[0]);
    return lines.slice(1).map(line => {
        const values = parseLine(line);
        const obj = {};
        headers.forEach((header, i) => {
            obj[header] = values[i] || '';
        });
        return obj;
    });
}

function getMostFrequent(arr) {
    if (!arr || arr.length === 0) return '';
    const counts = {};
    let maxCount = 0;
    let mostFreq = '';
    arr.forEach(val => {
        if (!val) return;
        const items = val.split(';').map(s => s.trim());
        items.forEach(item => {
            counts[item] = (counts[item] || 0) + 1;
            if (counts[item] > maxCount) {
                maxCount = counts[item];
                mostFreq = item;
            }
        });
    });
    return mostFreq;
}

// Get top N frequent items
function getTopItems(arr, n = 3) {
    if (!arr || arr.length === 0) return [];
    const counts = {};
    arr.forEach(val => {
        if (!val) return;
        const items = val.split(';').map(s => s.trim());
        items.forEach(item => {
            counts[item] = (counts[item] || 0) + 1;
        });
    });
    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, n)
        .map(entry => entry[0]);
}

const CLASSES = [
    { id: 'class_9_to_10', name: 'Class 9 to 10' },
    { id: 'class_8_to_9', name: 'Class 8 to 9' },
    { id: 'class_7_to_8', name: 'Class 7 to 8' },
    { id: 'class_6_to_7', name: 'Class 6 to 7' },
    { id: 'AOP_engineering', name: 'AOP Engineering' },
    { id: 'AOP_medical', name: 'AOP Medical' }
];

function App() {
    const [selectedClassId, setSelectedClassId] = useState(CLASSES[0].id);
    const [allStudents, setAllStudents] = useState([]);
    const [selectedStudentId, setSelectedStudentId] = useState('');
    const [isFixItOpen, setIsFixItOpen] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        fetch(`/Inputs/${selectedClassId}/student_insight_summary.csv`)
            .then(res => res.text())
            .then(text => {
                const data = parseCSV(text);
                setAllStudents(data);
                setSelectedStudentId('');
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load CSV:", err);
                setLoading(false);
            });
    }, [selectedClassId]);

    const classStats = useMemo(() => {
        if (allStudents.length === 0) return null;
        const accuracies = allStudents.map(s => parseFloat(s.accuracy_percentage) || 0);
        const avgAccuracy = Math.round(accuracies.reduce((a, b) => a + b, 0) / accuracies.length);

        return {
            avgAccuracy: `${avgAccuracy}%`,
            focusZone: getTopItems(allStudents.map(s => s.weakest_concepts)),
            steadyZone: getTopItems(allStudents.map(s => s.strongest_concepts)),
            topMistake: getMostFrequent(allStudents.map(s => s.dominant_mistake_pattern))
        };
    }, [allStudents]);

    const selectedStudent = useMemo(() => {
        return allStudents.find(s => s.student_id === selectedStudentId) || null;
    }, [allStudents, selectedStudentId]);

    if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontStyle: 'italic', color: 'var(--text-muted)' }}>Loading InzightEd Dashboard...</div>;

    return (
        <div className="app-container">
            {/* Top Header */}
            <header className="header">
                <div className="header-left">
                    <img src="/Assets/logo2.png" alt="Pace Academy" className="logo-pace" />
                </div>
                <div className="header-center desk-only">
                    <h1 className="header-title">InzightEd Dashboard</h1>
                </div>
                <div className="header-right">
                    <img src="/Assets/logo1.svg" alt="InzightEd" className="logo-inzighted" />
                </div>
            </header>

            {/* Top Bar - Class Selector */}
            <div className="top-bar">
                <select
                    className="class-selector"
                    value={selectedClassId}
                    onChange={(e) => setSelectedClassId(e.target.value)}
                >
                    {CLASSES.map(cls => (
                        <option key={cls.id} value={cls.id}>{cls.name}</option>
                    ))}
                </select>
            </div>

            <main className="main-content">
                {/* Left Panel — Class Overview */}
                <aside className="left-panel">
                    <h2 className="section-title">Class Overview</h2>

                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(120px, 1fr) 1.5fr', gap: '20px' }}>
                        <div className="accuracy-card">
                            <div className="accuracy-label">Avg. Accuracy</div>
                            <div className="accuracy-value">{classStats?.avgAccuracy || '0%'}</div>
                        </div>

                        <div className="zone-card">
                            <div className="zone-header">Focus Zone</div>
                            <div className="zone-content">
                                <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Top Weaknesses</div>
                                <ul className="zone-list">
                                    {classStats?.focusZone.map((item, i) => (
                                        <li key={i}>{item}</li>
                                    ))}
                                    {(!classStats || classStats.focusZone.length === 0) && <li>No data available</li>}
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div className="action-plan">
                        <div className="action-plan-header">Action Plan</div>
                        <div className="action-plan-content">
                            <ul className="zone-list">
                                {classStats?.topMistake ? (
                                    <>
                                        <li><strong>Primary Issue:</strong> {classStats.topMistake}</li>
                                        <li>Review {classStats.focusZone[0] || 'core concepts'} performance trends across all sections.</li>
                                        <li>Schedule remedial interventions for frequent mistake patterns.</li>
                                    </>
                                ) : (
                                    <li>Data collection in progress for this class.</li>
                                )}
                            </ul>
                        </div>
                    </div>

                    <div>
                        <h3 className="section-title" style={{ fontSize: '0.95rem' }}>Class Performance Summary</h3>
                        <div className="performance-table-container">
                            <table className="performance-table">
                                <thead>
                                    <tr>
                                        <th>Student ID</th>
                                        <th>Accuracy</th>
                                        <th>Top Weakness</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {allStudents.slice(0, 5).map(student => (
                                        <tr key={student.student_id}>
                                            <td>{student.student_id}</td>
                                            <td style={{ fontWeight: '600' }}>{student.accuracy_percentage}%</td>
                                            <td>{student.weakest_concepts?.split(';')[0] || '—'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </aside>

                {/* Right Panel — Student Analysis */}
                <section className="right-panel">
                    <h2 className="section-title">Student Analysis</h2>

                    <div className="student-bar">
                        <select
                            className="student-selector"
                            value={selectedStudentId}
                            onChange={(e) => {
                                setSelectedStudentId(e.target.value);
                            }}
                        >
                            <option value="">Select Student</option>
                            {allStudents.map(student => (
                                <option key={student.student_id} value={student.student_id}>Student ID: {student.student_id}</option>
                            ))}
                        </select>
                    </div>

                    {/* Fix It Zone - Static on Desktop, Collapsed Toggle on Mobile */}
                    <div className={`fix-it-zone ${isFixItOpen ? 'is-open' : 'is-collapsed'}`}>
                        <div className="fix-it-header" onClick={() => setIsFixItOpen(!isFixItOpen)}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '12px', fontWeight: '700' }}>
                                <span style={{ background: '#ef4444', height: '8px', width: '8px', borderRadius: '50%' }}></span>
                                Fix It Zone
                            </span>
                            <div className="mobile-only">
                                {isFixItOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                            </div>
                        </div>
                        <div className="fix-it-content">
                            {selectedStudent ? (
                                <>
                                    <h4 style={{ borderLeft: '4px solid #ef4444', paddingLeft: '12px' }}>{selectedStudent.dominant_mistake_pattern}</h4>
                                    <div className="fix-it-text">
                                        <p>{selectedStudent.llm_summary}</p>
                                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
                                            <div style={{ background: 'var(--text-dark)', color: 'white', borderRadius: '50%', padding: '6px', cursor: 'pointer', transition: 'transform 0.2s' }} onMouseEnter={e => e.currentTarget.style.transform = 'translateX(4px)'} onMouseLeave={e => e.currentTarget.style.transform = 'translateX(0)'}>
                                                <ArrowRight size={20} />
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <p style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Select a student to view detailed mistake patterns and recommendations.</p>
                            )}
                        </div>
                    </div>

                    <div className="student-accuracy-strip">
                        <span>Performance Snapshot</span>
                        <div className="accuracy-box">
                            <span className="accuracy-label-small">Accuracy:</span>
                            <span className="accuracy-percent">{selectedStudent?.accuracy_percentage ? `${selectedStudent.accuracy_percentage}%` : '—'}</span>
                        </div>
                    </div>

                    <div className="zone-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                        <div className="zone-card">
                            <div className="zone-header">Focus Zone</div>
                            <div className="zone-content">
                                <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', marginBottom: '8px', opacity: 0.8 }}>Areas to Improve</div>
                                <ul className="zone-list">
                                    {selectedStudent?.weakest_concepts ? (
                                        selectedStudent.weakest_concepts.split(';').slice(0, 3).map((item, i) => (
                                            <li key={i}>{item}</li>
                                        ))
                                    ) : (
                                        <li>Select a student to view weaknesses</li>
                                    )}
                                </ul>
                            </div>
                        </div>

                        <div className="zone-card">
                            <div className="zone-header">Steady Zone</div>
                            <div className="zone-content">
                                <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', marginBottom: '8px', opacity: 0.8 }}>Strongest Concepts</div>
                                <ul className="zone-list">
                                    {selectedStudent?.strongest_concepts ? (
                                        selectedStudent.strongest_concepts.split(';').slice(0, 3).map((item, i) => (
                                            <li key={i}>{item}</li>
                                        ))
                                    ) : (
                                        <li>Select a student to view strengths</li>
                                    )}
                                </ul>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}

export default App;
