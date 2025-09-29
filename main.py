import sys
from bot import ChatBot


BANNER = r"""
 ____ _           _   
/ ___| |__   __ _| |_ 
| |   | '_ \ / _` | __|
| |___| | | | (_| | |_ 
\____|_| |_|\__,_|\__|
"""

def main ():
    bot = ChatBot()
    print(BANNER)
    while True:
        try:
            user_input = input(">")
        except(KeyboardInterrupt, EOFError):
            print("\nÇıkılıyor...")
            break
        result = bot.process_input(user_input)
        rtype = result.get("type")
        resp = result.get("response")  
        if rtype == "text":
            print(resp)
            break
        elif rtype == "error":
            print(f"[HATA] {resp}")
        else:
            print(resp)
    print("Görüşürüz!")

if __name__ == "__main__":
    main()
