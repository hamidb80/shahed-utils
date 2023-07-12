import std/[strutils, sequtils, json, nre, htmlparser, random, macros]
import client, std/httpclient
import utils
import macroplus

# ----- consts -----

type
  Rial* = distinct int

# ----- convertors -----

func toBool*(i: int): bool =
  i == 1

func parseBool*(s: string): bool =
  toBool parseInt s

func parseRial*(s: string): Rial =
  Rial parseInt s

# ----- consts -----

const
  baseUrl* = "https://food.shahed.ac.ir"
  apiv0* = baseUrl & "/api/v0"

# ----- utils -----

func repl(match: RegexMatch): string =
  match.captures[0].entityToUtf8

func toHumanReadable(s: string): string =
  s.replace(re"&(\w+);", repl)

# ----- working with data objects -----

proc extractLoginPageData*(htmlPage: string): JsonNode =
  const
    headSig = "{&quot;loginUrl&quot"
    tailSig = ",&quot;custom&quot;:null}"

  let
    s = htmlPage.find headSig
    e = htmlPage.find tailSig

  htmlPage[s ..< e + tailSig.len]
  .toHumanReadable
  .parseJson

func extractLoginUrl*(loginPageData: JsonNode): string =
  baseUrl & loginPageData["loginUrl"].getStr

func extractLoginXsrfToken*(loginPageData: JsonNode): string =
  getStr loginPageData{"antiForgery", "value"}

func loginForm*(user, pass, captcha, token: string): auto =
  {
    "username": user,
    "password": pass,
    "Captcha": captcha,
    "idsrv.xsrf": token}

func cleanLoginCapcha*(binary: string): string =
  binary.cutAfter jpegTail

# ----- meta programming -----

template convertFn(t: type bool): untyped = parseBool
template convertFn(t: type int): untyped = parseInt
template convertFn(t: type Rial): untyped = parseRial
template convertFn(t: type JsonNode): untyped = parseJson


macro defAPI(pattern, typecast, url): untyped =
  let
    (name, extraArgs) =
      case pattern.kind
      of nnkIdent: (pattern, @[])
      of nnkObjConstr: (pattern[ObjConstrIdent], pattern[ObjConstrFields])
      else: raise newException(ValueError, "invalid API pattern: " &
          treeRepr pattern)

    body = quote:
      let data = c.sendData(apiv0 & `url`, accept = cJson).body
      convertFn(`typecast`)(data)

    args = extraArgs.mapIt newIdentDefs(it[0], it[1])

  newProc(name.exported,
    @[typecast, newIdentDefs(
      ident "c",
      newTree(nnkVarTy, ident "CustomHttpClient"))] & args,
    body)

# ----- API -----

const userPage* = baseUrl & "/#!/UserIndex"

proc freshCapchaUrl*: string =
  apiv0 & "/Captcha?id=" & $(rand 1..1000000)

defAPI isCapchaEnabled, bool, "/Captcha?isactive=wehavecaptcha"
defAPI credit, Rial, "/Credit"
defAPI reservation(week: int), JsonNode,
  "/Reservation?lastdate=&navigation=" & $(week*7)
