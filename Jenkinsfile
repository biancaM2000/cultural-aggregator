pipeline {
    agent any

    environment {
        // Define any environment variables here
        SERVER_IP = '18.192.12.98'
        SERVER_USER = 'ubuntu'
        APP_DIR = '/home/ubuntu/app'
    }   

    stages {
        stage('1. Verificare cod local') {
            steps {
                echo 'Analizare fisiere preluate din repository...'
                sh 'ls -la'
            }
        }       
        stage('2. Testare structura Docker') {
            steps {
                echo 'Se verifica integritatea retelei Dockerfile local...'
                sh 'sudo docker compose config'
            }
        }

        stage('3. Livrare in productie (AWS  EC2)') {   
            steps {
                echo 'Se initiaza copierea codului pe serverul AWS ${SERVER_IP}...'
                //Verific ca folderul destinatiei exista pe server, daca nu exista il creez, apoi copiez tot continutul proiectului
                sh "ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_proiect ${SERVER_USER}@${SERVER_IP} 'mkdir -p ${APP_DIR}'"
                //Copiez direct pe retea fisierele actualizate din proiect  
                sh "scp -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_proiect -r ./* ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/"

                echo 'Se reconstruiesc containerele izolate pe serverul AWS...'
                //Rulez curatatrea si reconstruirea direct in Cloud  
                sh """
                    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_proiect ${SERVER_USER}@${SERVER_IP} "
                        cd ${APP_DIR} &&
                        sudo docker compose down &&
                        sudo docker system prune -af &&
                        sudo docker compose up --build -d
                    "
                """
                }
            }
        }

    post {
        success {
            echo 'Pipeline finalizat cu succes!'
        }
        failure {
            echo 'Pipeline a esuat. Verificati logurile pentru detalii.'
        }
    }
}