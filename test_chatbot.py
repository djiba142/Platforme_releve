import requests

s = requests.Session()
url = "http://127.0.0.1:8000/chatbot/api/"

def run_tests():
    with open('test_chatbot_output.txt', 'w', encoding='utf-8') as f:
        def send_msg(text):
            f.write(f"\nUser: {text}\n")
            resp = s.post(url, json={"message": text})
            if resp.status_code == 200:
                data = resp.json()
                f.write(f"Bot (etat={data.get('etat')}): \n{data.get('reponse')}\n")
            else:
                f.write(f"Error HTTP {resp.status_code}\n")

        f.write("--- SCENARIO 1: RELEVE ---\n")
        send_msg("Je veux mon relevé")
        send_msg("22NT001") # Might fail if not exist, will create if needed
        send_msg("1")

        s.cookies.clear() # Reset session
        f.write("\n--- SCENARIO 2: NOTES ---\n")
        send_msg("Afficher mes notes")
        send_msg("22DL003") 

        s.cookies.clear()
        f.write("\n--- SCENARIO 3: OUBLI MDP ---\n")
        send_msg("J'ai oublié mon mot de passe")
        send_msg("22NT010")

        s.cookies.clear()
        f.write("\n--- SCENARIO 4: FILIERE ---\n")
        send_msg("Parlez-moi de NTIC")
        send_msg("Parlez moi de DL")
        
        s.cookies.clear()
        f.write("\n--- SCENARIO 5: CONTACT ---\n")
        send_msg("Comment contacter la scolarité ?")

        s.cookies.clear()
        f.write("\n--- SCENARIO 6: AIDE CONNEXION ---\n")
        send_msg("Je ne peux pas me connecter")
        send_msg("2")

if __name__ == '__main__':
    run_tests()
