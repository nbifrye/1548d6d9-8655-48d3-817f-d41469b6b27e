---
layout: post
title: "OAuth 2.0 Resource Owner Password Credentials Grant：RFC 6749 のフローと RFC 9700 の禁止要件"
date: 2026-09-22 02:42:00 +0900
categories: [authorization, oauth]
---

## この記事について

**記事タイプ:** Version Difference / Requirement  
**対象読者:** OAuth 2.0 の既存実装や移行対象で Resource Owner Password Credentials Grant（ROPC）を確認する開発者・レビュー担当者  
**この記事で伝えること:** RFC 6749 が定義した ROPC の request 構造と、RFC 9700 が現在の Best Current Practice としてその利用を禁止していること  
**扱わないこと:** Authorization Code Grant、Client Credentials Grant、Refresh Token の保護、Resource Owner の authentication method、ROPC から別方式への移行手順

## Article brief

- **Reader:** ROPC を含む OAuth 2.0 実装・仕様書を確認する開発者・レビュー担当者
- **Question:** RFC 6749 の ROPC はどのような Token Request であり、RFC 9700 によって規範要件はどう変わったか
- **Answer:** RFC 6749 §4.3.2 の request 構造と、RFC 9700 §2.4 の `MUST NOT` を区別して説明できる
- **Scope:** RFC 6749 §4.3–§4.3.3 と RFC 9700 §2.4
- **Out of scope:** 他の grant の詳細、移行方式の選定、deployment 固有の代替設計
- **Primary sources:** RFC 6749 §4.3–§4.3.3、RFC 9700 §2.4
- **Diagram:** Resource Owner → Client → Token Endpoint の credential / token の流れ

## 1. RFC 6749 が定義した ROPC

RFC 6749 §4.3 は、Resource Owner が Client に username と password を渡し、Client がそれらを Token Endpoint に提示して Access Token を取得する grant を定義しています。

RFC 6749 §4.3.1 では、Client が Access Token を取得した後、Resource Owner の credentials を破棄しなければならないと規定しています（MUST）。Client が credentials を取得する方法自体は RFC 6749 の scope 外です。

<pre class="mermaid">
flowchart TD
    RO[Resource Owner] -->|username / password| C[Client]
    C -->|Token Request| AS[Authorization Server]
    AS -->|Access Token| C
</pre>

この図は RFC 6749 §4.3 の処理関係を簡略化した非規範的な図です。

## 2. Token Request の parameter 配置

RFC 6749 §4.3.2 では、Client は Token Endpoint に request を送り、parameter を UTF-8 の `application/x-www-form-urlencoded` request body に配置します。

- `grant_type`: REQUIRED。値は `password` でなければなりません（MUST）。
- `username`: REQUIRED。Resource Owner の username です。
- `password`: REQUIRED。Resource Owner の password です。
- `scope`: OPTIONAL。RFC 6749 §3.3 の scope です。

Client が confidential client である場合、または client credentials やその他の authentication requirement を割り当てられている場合、Client は RFC 6749 §3.2.1 に従って Authorization Server に対して authentication を行わなければなりません（MUST）。

次は配置を示すための**非規範的な例**です。値は illustrative value です。

```http
POST /token HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=illustrative-user&password=illustrative-password&scope=read
```

この例は Client authentication が必要かどうかを示すものではありません。その要否は RFC 6749 §4.3.2 の条件に従います。

## 3. Access Token Response

RFC 6749 §4.3.3 は、request が valid で authorized である場合、Authorization Server が RFC 6749 §5.1 に従って Access Token と optional な Refresh Token を発行すると規定しています。request が client authentication に失敗した場合や invalid である場合は §5.2 の error response を返します。

successful response と error response の JSON 構造は、それぞれ既存の Token Endpoint response 記事のテーマであるため、ここでは展開しません。

## 4. RFC 9700 は ROPC の利用を禁止する

RFC 9700 §2.4 は、Resource Owner Password Credentials Grant について **MUST NOT be used** と規定しています。したがって、RFC 6749 に protocol flow が定義されていることと、現在の Best Current Practice において利用が認められていることは同義ではありません。

RFC 9700 §2.4 は理由として、Resource Owner の credentials が Client に露出することによる attack surface の増加と、Authorization Server 以外の場所へ credentials を入力する行動を利用者に求める点を挙げています。また、この grant は two-factor authentication や複数の user interaction step を必要とする authentication process を想定していないと説明しています。

**The protocol remains specified in RFC 6749, while RFC 9700 says it MUST NOT be used.**  
（このプロトコルは RFC 6749 に仕様として残っていますが、RFC 9700 は利用してはならないと規定しています。）

## 5. 仕様を読むときの区別

RFC 6749 §4.3–§4.3.3 は ROPC の wire-level protocol を定義しています。一方、RFC 9700 §2.4 はその grant の利用可否について現在の Best Current Practice の規範要件を示しています。

この記事では代替 grant や migration architecture を選定しません。それらは ROPC の request 構造と禁止要件という本記事の Question から外れるためです。

## Primary sources

- RFC 6749, §4.3–§4.3.3, *The OAuth 2.0 Authorization Framework*: https://www.rfc-editor.org/rfc/rfc6749.html
- RFC 9700, §2.4, *Best Current Practice for OAuth 2.0 Security*: https://www.rfc-editor.org/rfc/rfc9700.html
