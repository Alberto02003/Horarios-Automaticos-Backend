pipeline {
    agent any

    environment {
        RAILWAY_TOKEN = credentials('233783da-ab0b-49d3-baa6-5c7e486eb41e')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install') {
            steps {
                sh 'pip install uv && uv sync --extra dev'
            }
        }

        stage('Lint') {
            steps {
                sh 'uv run python -m py_compile src/main.py'
            }
        }

        stage('Test') {
            steps {
                sh 'uv run pytest tests/ -v --tb=short --junitxml=reports/test-results.xml'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/test-results.xml'
                }
            }
        }

        stage('Deploy to Railway') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    npm install -g @railway/cli || true
                    railway up --detach
                '''
            }
        }
    }

    post {
        success {
            echo 'Backend pipeline completed successfully.'
        }
        failure {
            echo 'Backend pipeline failed — check the logs above.'
        }
    }
}
