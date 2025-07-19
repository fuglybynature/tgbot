import requests
from bs4 import BeautifulSoup

def fetch_transfers(limit=10):
    url = "https://www.transfermarkt.com/transfers/neuestetransfers/statistik/plus/?plus=0&galerie=0&wettbewerb_id=alle&land_id=&selectedOptionInternalType=allFirstLeaguesWorldwide&minMarktwert=10.000.000&maxMarktwert=500.000.000&minAbloese=10.000.000&maxAbloese=500.000.000&yt0=%D0%9F%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B8+"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    leagues_to_remove = [
        "Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1",
        "Eredivisie", "Liga Portugal", "Belgian Pro League", "Jupiler Pro League",
        "Super Lig", "Russian Premier Liga", "Ukrainian Premier League", "Swiss Super League",
        "Austrian Bundesliga", "Scottish Premiership", "Greek Super League",
        "MLS", "Liga MX", "Liga MX Apertura", "Liga MX Clausura", "Brasileirão", "Série A", "Primera División",
        "Argentine Primera División", "Chilean Primera División", "Colombian Primera A",
        "Saudi Pro League", "Qatar Stars League", "Chinese Super League", "J1 League", "K League 1",
        "Egyptian Premier League", "Botola Pro", "Tunisian Ligue Professionnelle 1",
        "A-League", "Indian Super League", "USL Championship", "Czech First League", "Polish Ekstraklasa",
        "Danish Superliga", "Norwegian Eliteserien", "Swedish Allsvenskan", "Romanian Liga I",
        "Hungarian NB I", "Slovak Super Liga", "Slovenian PrvaLiga", "Bulgarian First League",
        "Serbian SuperLiga", "Croatian HNL", "Cypriot First Division", "Israeli Premier League",
        "Kazakhstan Premier League", "Uzbekistan Super League", "Thai League 1", "Vietnamese V.League 1", "Super liga Srbije", "Eliteserien"
        
    
    ]

    def clean_club_name(text):
        for league in leagues_to_remove:
            text = text.replace(league, "")
        return text.strip()

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.items tbody tr")

        if not rows:
            return "⚠️ No transfer rows found. Possibly blocked or HTML structure changed."

        messages = []
        count = 0

        for row in rows:
            if count >= limit:
                break

            try:
                cols = row.find_all("td", recursive=False)
                if len(cols) < 6:
                    continue

                name_tag = cols[0].select_one("table tr:first-child td:nth-child(2) a")
                player_name = name_tag.get_text(strip=True) if name_tag else cols[0].get_text(strip=True).split(":")[0]

                from_club = clean_club_name(cols[3].get_text(strip=True))
                to_club = clean_club_name(cols[4].get_text(strip=True))
                fee = cols[5].get_text(strip=True)

                messages.append(f"💰 *{player_name}*: {from_club} → {to_club} за *{fee}*")
                count += 1

            except Exception:
                continue

        return "\n".join(messages) if messages else "⚠️ No valid transfers found."

    except Exception as e:
        return f"❌ Error fetching transfers: {str(e)}"
