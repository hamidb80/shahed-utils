import html
from requests import Session as HttpSession
from random import randint
import json
from urllib.parse import urlencode
import re
from bs4 import BeautifulSoup

baseUrl = "https://food.shahed.ac.ir"
apiv0 = baseUrl + "/api/v0"

foods = {
    "ماکارونی": "🍝",  # Spaghetti
    "مرغ": "🍗",            # Chicken
    "کره": "🧈",            # Butter
    "ماهی": "🐟",          # Fish
    "برنج": "🍚",          # Rice
    "پلو": "🍚",            # Rice
    "میگو": "🦐",          # Shrimp
    "خورشت": "🍛",        # Stew
    "کوکو": "🧆",          # koo koooooo
    "کتلت": "🥮",          # cutlet
    "زیره": "🍘",          # Caraway
    "رشته": "🍜",          # str
    "کباب": "🥓",          # Kebab
    "ماهیچه": "🥩",      # Muscle
    "مرگ": "💀",            # Death
    "خالی": "🍽️",       # Nothing
    "گوجه": "🍅",          # Tomamto
    "سوپ": "🥣",            # Soup
    "قارچ": "🍄",          # Mushroom
    "کرفس": "🥬",          # Leafy Green
    "بادمجان": "🍆",    # Eggplant
    "هویج": "🥕",          # Carrot
    "پیاز": "🧅",          # Onion
    "سیب زمینی": "🥔",  # Potato
    "سیر": "🧄",            # Garlic
    "لیمو": "🍋",          # Lemon
    "آلو": "🫐",            # Plum
    "زیتون": "🫒",        # Olive

    "دوغ": "🥛",            # Dough
    "ماست": "⚪",           # Yogurt
    "دلستر": "🍺",        # Beer
    "سالاد": "🥗",        # Salad
    "نمک": "🧂",            # Salt
    "یخ": "🧊",              # Ice
}


# ----- working with data objects -----


def entity_to_utf8(entity: str):
    return entity.replace("&quot;", '"')


def extractLoginPageData(htmlPage: str) -> dict:
    headSig = b"{&quot;loginUrl&quot"
    tailSig = b",&quot;custom&quot;:null}"
    s = htmlPage.find(headSig)
    e = htmlPage.find(tailSig)
    content = htmlPage[s:e + len(tailSig)]
    bbbb = entity_to_utf8(str(content)[2:-1])
    return json.loads(bbbb)


def extractLoginUrl(loginPageData: dict) -> str:
    return baseUrl + loginPageData["loginUrl"]


def extractLoginXsrfToken(loginPageData: dict) -> str:
    return loginPageData["antiForgery"]["value"]


def loginForm(user, passw, captcha, token: str):
    return {
        "username": user,
        "password": passw,
        "Captcha": captcha,
        "idsrv.xsrf": token
    }


def cleanLoginCaptcha(binary: str) -> str:
    jpegTail = b"\xff\xd9"
    i = binary.find(jpegTail)
    return binary[0:i+2]


def genRedirectTransactionForm(data: dict):
    # Code: <StatusCode>,
    # Result: <Msg>,
    # Action: <RedirectUrl>,
    # ActionType: <HttpMethod>,
    # Tokenitems: Array[FormInput]
    # {"Name": "...", "Value": "..."}

    # buildHtml tdiv:
    #     form(
    #         id="X",
    #         action=getstr data["Action"],
    #       `method`=getstr data["ActionType"]
    #     ):
    #         for token in data["Tokenitems"]:
    #             input(
    #                 name=getstr token["Name"],
    #                 value=getstr token["Value"])

    #     script:
    #         verbatim "document.getElementById('X').submit()"

    return "<html></html>"


def freshCaptchaUrl() -> str:
    return apiv0 + "/Captcha?id=" + str(randint(1, 10000))


# tuple[loginPageData: dict, captchaBinary: str] =
def loginBeforeCaptcha(c: HttpSession):
    resp = c.get(baseUrl)
    assert resp.status_code in range(200, 300)

    a = extractLoginPageData(resp.content)

    r = c.get(
        freshCaptchaUrl(),
        headers={"Referer": resp.url}
    ).content

    b = cleanLoginCaptcha(r)

    return (a, b)


def loginAfterCaptcha(c: HttpSession,
                      loginPageData: dict,
                      uname, passw, capcha: str):

    resp = c.post(
        extractLoginUrl(loginPageData),
        data=loginForm(
            uname, passw, capcha,
            extractLoginXsrfToken(loginPageData)
        ))

    assert resp.status_code in range(200, 300)

    html = BeautifulSoup(resp.text, "html.parser")
    form = html.find("form")
    url = form["action"]
    inputs = [(el["name"], el["value"]) for el in form.find_all("input")]

    if url.startswith("{{"):
        raise "login failed"
    else:
        resp = c.post(url, data=inputs)
        assert resp.status_code in range(200, 300)


def getCredit(c: HttpSession):
    return c.get(apiv0 + "/Credit").content


if __name__ == "__main__":
    s = HttpSession()
    (login_data, capcha_binary) = loginBeforeCaptcha(s)

    f = open("c.png", "wb")
    f.write(capcha_binary)
    f.close()

    loginAfterCaptcha(
        s,
        login_data, "992164012", "@123456789",
        input("read capcha: "))

    print(getCredit(s))