/**
 * EduInsight 智绘学途
 * Student Profile & Academic Planning System
 * Main Application Logic
 */

const StudentApp = {
    state: {
        currentStudentId: null,
        students: [],
        charts: {
            radar: null,
            comparison: null
        }
    },

    api: {
        baseUrl: '/api',
        
        async getAllStudents() {
            const response = await fetch(`${this.baseUrl}/students/`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        },

        async getStudentBasic(id) {
            const response = await fetch(`${this.baseUrl}/student/${id}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        },

        async getStudentDetails(id) {
            const response = await fetch(`${this.baseUrl}/student/${id}/details`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        },

        async getStudentPlan(id) {
            const response = await fetch(`${this.baseUrl}/student/${id}/plan`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        }
    },

    init() {
        this.cacheDOM();
        this.bindEvents();
        this.loadInitialData();
    },

    cacheDOM() {
        this.dom = {
            studentSelect: document.getElementById('student-select'),
            viewStudentBtn: document.getElementById('view-student'),
            studentDetails: document.getElementById('student-details'),
            allStudentsTable: document.getElementById('all-students-table'),
            
            // Basic Info
            studentId: document.getElementById('student-id'),
            studentType: document.getElementById('student-type'),
            knowledgeScore: document.getElementById('knowledge-score'),
            cognitionScore: document.getElementById('cognition-score'),
            affectionScore: document.getElementById('affection-score'),
            behaviorScore: document.getElementById('behavior-score'),
            
            // Charts
            radarChart: document.getElementById('student-radar-chart'),
            comparisonChart: document.getElementById('comparison-radar-chart'),
            
            // Recommendations
            recKnowledge: document.getElementById('knowledge-recommendations'),
            recCognitive: document.getElementById('cognitive-recommendations'),
            recAffective: document.getElementById('affective-recommendations'),
            recBehavioral: document.getElementById('behavioral-recommendations')
        };
    },

    bindEvents() {
        this.dom.studentSelect.addEventListener('change', (e) => {
            this.state.currentStudentId = e.target.value;
            // 自动加载选中的学生
            this.updateStudentDisplay(this.state.currentStudentId);
        });

        this.dom.viewStudentBtn.addEventListener('click', (e) => {
            e.preventDefault(); // 防止可能的表单提交
            if (this.state.currentStudentId) {
                this.updateStudentDisplay(this.state.currentStudentId);
            } else {
                alert('请先选择一个学生');
            }
        });
    },

    async loadInitialData() {
        try {
            const students = await this.api.getAllStudents();
            this.state.students = students;
            
            this.renderStudentSelect(students);
            this.renderAllStudentsTable(students);

            // Select first student by default or specific ID if exists
            if (students.length > 0) {
                const defaultId = 34400002;
                const exists = students.some(s => s.student_id == defaultId);
                this.state.currentStudentId = exists ? defaultId : students[0].student_id;
                
                this.dom.studentSelect.value = this.state.currentStudentId;
                this.updateStudentDisplay(this.state.currentStudentId);
            }
        } catch (error) {
            console.error('Initialization error:', error);
            this.dom.studentDetails.innerHTML = `<div class="p-4 bg-red-50 text-red-700 rounded-md">系统初始化失败: ${error.message}</div>`;
        }
    },

    renderStudentSelect(students) {
        this.dom.studentSelect.innerHTML = '';
        students.forEach(student => {
            const option = document.createElement('option');
            option.value = student.student_id;
            option.textContent = `学生 ${student.student_id} - ${student.student_type}`;
            this.dom.studentSelect.appendChild(option);
        });
    },

    renderAllStudentsTable(students) {
        this.dom.allStudentsTable.innerHTML = '';
        
        students.forEach(student => {
            const row = document.createElement('tr');
            row.className = 'student-table-row hover:bg-gray-50 transition-colors';
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-600">${student.student_id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${this.getTypeClass(student.student_type)}">
                        ${student.student_type}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">${student.knowledge_score?.toFixed(2) || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">${student.cognitive_score?.toFixed(2) || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">${student.affective_score?.toFixed(2) || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">${student.behavioral_score?.toFixed(2) || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                    <button class="text-indigo-600 hover:text-indigo-900 view-student-btn" data-id="${student.student_id}">
                        查看详情
                    </button>
                </td>
            `;
            this.dom.allStudentsTable.appendChild(row);
        });

        // Bind click events for table buttons
        document.querySelectorAll('.view-student-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.getAttribute('data-id');
                this.dom.studentSelect.value = id;
                this.state.currentStudentId = id;
                this.updateStudentDisplay(id);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    },

    async updateStudentDisplay(studentId) {
        if (!studentId) return;

        // Reset UI & Show Loading
        this.setLoadingState(true);

        try {
            // 1. Fetch Basic Data
            const basicData = await this.api.getStudentBasic(studentId);
            this.renderBasicInfo(basicData);
            this.updateCharts(basicData);

            // 2. Fetch Detailed Data (Parallel request for Plan and Details)
            const [detailsData, planData] = await Promise.allSettled([
                this.api.getStudentDetails(studentId),
                this.api.getStudentPlan(studentId)
            ]);

            // Handle Details
            if (detailsData.status === 'fulfilled') {
                this.renderExpertDiagnosis(detailsData.value);
            } else {
                this.renderExpertDiagnosisError(detailsData.reason);
            }

            // Handle Plan
            if (planData.status === 'fulfilled') {
                this.renderRecommendations(planData.value);
            } else {
                this.renderRecommendationsError(planData.reason);
            }

        } catch (error) {
            console.error('Error updating display:', error);
            this.dom.studentDetails.innerHTML = `<div class="text-red-500 p-4">加载数据失败: ${error.message}</div>`;
        } finally {
            this.setLoadingState(false);
        }
    },

    setLoadingState(isLoading) {
        if (isLoading) {
            // Add loading skeletons or indicators
            const skeleton = '<div class="h-4 bg-gray-200 rounded w-3/4 animate-pulse"></div>';
            this.updateRecCard(this.dom.recKnowledge, [skeleton]);
            this.updateRecCard(this.dom.recCognitive, [skeleton]);
            this.updateRecCard(this.dom.recAffective, [skeleton]);
            this.updateRecCard(this.dom.recBehavioral, [skeleton]);
            
            // Safety check for expert diagnosis element
            const diagnosisEl = document.getElementById('expert-diagnosis');
            if (diagnosisEl) {
                diagnosisEl.innerHTML = `
                    <div class="space-y-3">
                        <div class="h-4 bg-gray-200 rounded w-full animate-pulse"></div>
                        <div class="h-4 bg-gray-200 rounded w-5/6 animate-pulse"></div>
                        <div class="h-4 bg-gray-200 rounded w-4/6 animate-pulse"></div>
                    </div>
                `;
            }
        }
    },

    renderBasicInfo(data) {
        this.dom.studentId.textContent = data.student_id || 'N/A';
        this.dom.studentType.textContent = data.student_type || '待分类';
        this.dom.studentType.className = `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${this.getTypeClass(data.student_type)}`;
        
        this.dom.knowledgeScore.textContent = data.knowledge_score ?? '-';
        this.dom.cognitionScore.textContent = data.cognitive_score ?? '-';
        this.dom.affectionScore.textContent = data.affective_score ?? '-';
        this.dom.behaviorScore.textContent = data.behavioral_score ?? '-';

        // Render detailed metrics
        let detailsHTML = `
            <div class="mb-6">
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                    <i class="fas fa-user-md mr-2 text-indigo-600"></i>专家诊断
                </h3>
                <div id="expert-diagnosis" class="text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-100 min-h-[100px]"></div>
            </div>
            
            <div>
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                    <i class="fas fa-chart-bar mr-2 text-indigo-600"></i>详细指标
                </h3>
        `;
        
        if (data.detail_metrics && data.detail_metrics.length > 0) {
            detailsHTML += '<div class="grid grid-cols-2 gap-2 text-sm">';
            data.detail_metrics.forEach(metric => {
                detailsHTML += `
                    <div class="flex justify-between p-2 bg-gray-50 rounded">
                        <span class="text-gray-600">${metric.name}</span>
                        <span class="font-medium text-gray-900">${metric.value}</span>
                    </div>`;
            });
            detailsHTML += '</div></div>';
        } else {
            detailsHTML += '<p class="text-gray-500 italic">暂无详细指标信息。</p></div>';
        }
        
        this.dom.studentDetails.innerHTML = detailsHTML;
    },

    renderExpertDiagnosis(data) {
        const el = document.getElementById('expert-diagnosis');
        if (data.expert_diagnosis) {
            el.innerHTML = marked.parse(data.expert_diagnosis);
        } else {
            el.innerHTML = '<p class="text-gray-500 italic">暂无专家诊断。</p>';
        }
    },

    renderExpertDiagnosisError(error) {
        document.getElementById('expert-diagnosis').innerHTML = `<p class="text-red-500">加载诊断失败: ${error}</p>`;
    },

    renderRecommendations(data) {
        // Clean up newlines in data
        for (const key in data) {
            if (typeof data[key] === 'string') {
                data[key] = data[key].replace(/\n\n/g, '\n');
            }
        }

        const parseRecs = (text) => (typeof text === 'string' && text.trim().length > 0) ? text.split('\n') : [];

        this.updateRecCard(this.dom.recKnowledge, parseRecs(data["知识维度"]));
        this.updateRecCard(this.dom.recCognitive, parseRecs(data["认知维度"]));
        this.updateRecCard(this.dom.recAffective, parseRecs(data["情感维度"]));
        this.updateRecCard(this.dom.recBehavioral, parseRecs(data["行为维度"]));
    },

    renderRecommendationsError(error) {
        const msg = `<span class="text-red-500">加载失败</span>`;
        this.updateRecCard(this.dom.recKnowledge, [msg]);
        this.updateRecCard(this.dom.recCognitive, [msg]);
        this.updateRecCard(this.dom.recAffective, [msg]);
        this.updateRecCard(this.dom.recBehavioral, [msg]);
    },

    updateRecCard(element, items) {
        if (!element) return;
        element.innerHTML = '';
        
        if (items && items.length > 0) {
            items.forEach(item => {
                // Check if item is HTML (like skeleton or error)
                if (item.includes('<')) {
                     const div = document.createElement('div');
                     div.innerHTML = item;
                     element.appendChild(div);
                } else {
                    const li = document.createElement('li');
                    li.className = 'flex items-start group';
                    li.innerHTML = `
                        <i class="fas fa-check-circle mt-1 mr-2 text-green-500 group-hover:text-green-600 transition-colors"></i>
                        <span class="text-gray-700 leading-relaxed">${marked.parse(item)}</span>
                    `;
                    element.appendChild(li);
                }
            });
        } else {
            element.innerHTML = '<li class="text-gray-400 italic">暂无建议</li>';
        }
    },

    getTypeClass(type) {
        const map = {
            '优秀全面型': 'bg-green-100 text-green-800 border border-green-200',
            '高压成绩型': 'bg-yellow-100 text-yellow-800 border border-yellow-200',
            '潜力型': 'bg-blue-100 text-blue-800 border border-blue-200',
            '警示型': 'bg-red-100 text-red-800 border border-red-200',
            '待分类': 'bg-gray-100 text-gray-800 border border-gray-200'
        };
        return map[type] || 'bg-gray-100 text-gray-800';
    },

    updateCharts(data) {
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return;
        }

        // Destroy existing charts
        if (this.state.charts.radar) this.state.charts.radar.destroy();
        if (this.state.charts.comparison) this.state.charts.comparison.destroy();

        const commonOptions = {
            scales: {
                r: {
                    min: 0,
                    max: 100,
                    ticks: { stepSize: 20, display: false },
                    pointLabels: {
                        font: { size: 12, family: "'Inter', sans-serif" }
                    }
                }
            },
            plugins: {
                legend: { position: 'bottom' }
            },
            maintainAspectRatio: false
        };

        // Ensure scores are numbers
        const values = [
            Number(data.knowledge_score) || 0,
            Number(data.cognitive_score) || 0,
            Number(data.affective_score) || 0,
            Number(data.behavioral_score) || 0
        ];

        try {
            // 1. Personal Radar
            const radarCtx = this.dom.radarChart.getContext('2d');
            this.state.charts.radar = new Chart(radarCtx, {
                type: 'radar',
                data: {
                    labels: ['知识维度', '认知维度', '情感维度', '行为维度'],
                    datasets: [{
                        label: '个人得分',
                        data: values,
                        backgroundColor: 'rgba(79, 70, 229, 0.2)',
                        borderColor: 'rgba(79, 70, 229, 1)',
                        pointBackgroundColor: 'rgba(79, 70, 229, 1)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(79, 70, 229, 1)'
                    }]
                },
                options: commonOptions
            });

            // 2. Comparison Radar
            const comparisonCtx = this.dom.comparisonChart.getContext('2d');
            this.state.charts.comparison = new Chart(comparisonCtx, {
                type: 'radar',
                data: {
                    labels: ['知识维度', '认知维度', '情感维度', '行为维度'],
                    datasets: [
                        {
                            label: '个人得分',
                            data: values,
                            backgroundColor: 'rgba(79, 70, 229, 0.2)',
                            borderColor: 'rgba(79, 70, 229, 1)',
                            pointBackgroundColor: 'rgba(79, 70, 229, 1)'
                        },
                        {
                            label: '班级平均',
                            data: [77, 77.2, 78.8, 73.2], // Fixed averages for now
                            backgroundColor: 'rgba(156, 163, 175, 0.2)',
                            borderColor: 'rgba(156, 163, 175, 1)',
                            pointBackgroundColor: 'rgba(156, 163, 175, 1)'
                        }
                    ]
                },
                options: commonOptions
            });
        } catch (e) {
            console.error("Error rendering charts:", e);
        }
    }
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    StudentApp.init();
});
