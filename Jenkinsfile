pipeline {
    agent any

    environment {
        SERVER_IP = '18.192.12.98'
        SERVER_USER = 'ubuntu'
        APP_DIR = '/home/ubuntu/app'
        // Calea cheii private securizate pentru Jenkins
        SSH_KEY = '/var/lib/jenkins/.ssh/id_rsa_proiect'
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

        stage('3. Livrare in productie (AWS EC2)') {   
            steps {
                echo "Se initiaza copierea codului pe serverul AWS ${SERVER_IP}..."
                
                // Verific daca directorul exista si daca nu, il creeaza in siguranta
                sh "ssh -o StrictHostKeyChecking=no -i ${SSH_KEY} ${SERVER_USER}@${SERVER_IP} 'mkdir -p ${APP_DIR}'"
                
                // Copiez tot codul sursa, inclusiv Dockerfile si docker-compose.yml, in siguranta pe serverul AWS
                sh "scp -o StrictHostKeyChecking=no -i ${SSH_KEY} -r ./* .dockerignore ${SERVER_USER}@${SERVER_IP}:${APP_DIR}/"

                echo 'Se reconstruiesc containerele izolate pe serverul AWS...'
                // Rulez comanda de deploy pe serverul AWS, asigurandu-ma ca folosesc cheia privata pentru autentificare si ca execut comenzile in siguranta
                sh """
                    ssh -o StrictHostKeyChecking=no -i ${SSH_KEY} ${SERVER_USER}@${SERVER_IP} "
                        cd ${APP_DIR} &&
                        sudo docker compose down --remove-orphans &&
                        sudo docker system prune -af &&
                        sudo docker compose up --build -d
                    "
                """
            }
        }
    }

    post {
        success {
            echo 'Pipeline finalizat cu succes! Aplicatia e actualizata pe AWS EC2.' 
        }
        failure {
            echo 'Pipeline a esuat. Verificati logurile pentru detalii legate de permisiuni sau conexiune.'
        }
    }
}