---
layout: post
title: "OAuth redirect_uri validation：登録要件と exact string matching"
date: 2026-09-22 05:46:00 +0900
categories: [authorization, oauth]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** OAuth の Authorization Endpoint で `redirect_uri` の登録・検証を実装またはレビューする開発者  
**この記事で伝えること:** RFC 6749 の redirection endpoint 登録・`redirect_uri` 検証要件と、RFC 9700 が現在要求する exact string matching  
**扱わないこと:** Authorization Code Grant 全体、PKCE、open redirector の詳細、native app の redirect URI 設計、PAR/JAR の詳細

## Article brief

- **Reader:** Authorization Endpoint の `redirect_uri` 検証を実装・レビューする開発者
- **Question:** Client が送る `redirect_uri` を Authorization Server は登録済み URI とどのように照合し、不一致時にどう処理する必要があるか
- **Answer:** `redirect_uri` の配置、RFC 6749 の登録・照合要件、RFC 9700 の exact string matching と localhost native app の例外、不一致時に invalid URI へ redirect しない要件を区別できる
- **Scope:** RFC 6749 §3.1.2.2–§3.1.2.4、RFC 9700 §2.1・§4.1.3
- **Out of scope:** grant 全体、PKCE、open redirector の詳細、native app の URI scheme 選択、PAR/JAR の protocol flow
- **Primary sources:** RFC 6749 §3.1.2.2–§3.1.2.4、RFC 9700 §2.1・§4.1.3
- **Diagram:** Authorization Request の `redirect_uri` と登録済み URI の照合、成功時の redirect、不一致時の停止

## 1. `redirect_uri` は Authorization Request に置かれる

RFC 6749 §3.1.2.3 では、複数の redirection URI が登録されている場合、URI の一部だけが登録されている場合、または URI が登録されていない場合、Client は Authorization Request に `redirect_uri` request parameter を含めなければなりません（**MUST**）。

次は配置を示すための**非規範的な例**です。値は illustrative value です。

```http
GET /authorize?response_type=code&client_id=illustrative-client&redirect_uri=https%3A%2F%2Fclient.example%2Fcallback HTTP/1.1
Host: authorization.example
```

`redirect_uri` は Authorization Endpoint への request parameter であり、この例では URI の query component に配置されています。

## 2. RFC 6749 の登録要件

RFC 6749 §3.1.2.2 では、Authorization Server は public client と Implicit Grant を利用する confidential client に redirection endpoint の登録を要求しなければなりません（**MUST**）。また、Authorization Server は Authorization Endpoint を利用するすべての Client に事前登録を要求すべきです（**SHOULD**）。

同 section は、Authorization Server が完全な redirection URI の登録を要求すべきこと（**SHOULD**）と、複数の redirection endpoint の登録を許可できること（**MAY**）も規定しています。

## 3. RFC 6749 の照合と RFC 9700 の exact matching

RFC 6749 §3.1.2.3 では、Authorization Request に `redirect_uri` が含まれ、redirection URI が登録されている場合、Authorization Server は受信値を登録値と照合しなければなりません（**MUST**）。完全な redirection URI が登録されている場合は、RFC 3986 §6.2.1 の simple string comparison を使用しなければなりません（**MUST**）。

RFC 9700 §2.1 は現在の Best Current Practice として、事前登録された client redirection URI との比較に exact string matching を使用しなければならないと規定しています（**MUST**）。例外は native app の `localhost` redirection URI における port number で、RFC 9700 §4.1.3 は RFC 8252 §7.3 に従って可変 port number を許可しなければならないと規定しています（**MUST**）。

**Exact matching is the current BCP requirement; it is not merely an implementation preference.**  
（exact matching は現在の BCP における要件であり、単なる実装上の選好ではありません。）

## 4. 不一致なら invalid URI へ redirect しない

RFC 6749 §3.1.2.4 は、missing、invalid、または mismatching redirection URI により Authorization Request の validation が失敗した場合、Authorization Server は Resource Owner に error を知らせるべきと規定しています（**SHOULD**）。同時に、invalid redirection URI へ User-Agent を自動 redirect してはなりません（**MUST NOT**）。

<pre class="mermaid">
flowchart TD
    A[Authorization Request] --> B[redirect_uri を登録値と照合]
    B -->|一致| C[Authorization 処理を継続]
    B -->|不一致| D[Request validation 失敗]
    D --> E[invalid URI へ redirect しない]
</pre>

この図は RFC 6749 §3.1.2.3–§3.1.2.4 と RFC 9700 §2.1 の関係を簡略化した**非規範的な図**です。

## 5. 仕様上の境界

RFC 9700 §4.1.3 は、Authorization Request に含まれる redirection URI の origin と integrity を検証できる場合、たとえば RFC 9101 または client authentication を伴う RFC 9126 を使用する場合、Authorization Server が追加の redirection URI check を行わず、その URI を信頼してもよいと規定しています（**MAY**）。この記事では、その条件を満たす deployment の選択を推奨しません。

## Primary sources

- RFC 6749, §3.1.2.2–§3.1.2.4, *The OAuth 2.0 Authorization Framework*: https://www.rfc-editor.org/rfc/rfc6749.html
- RFC 9700, §2.1, §4.1.3, *Best Current Practice for OAuth 2.0 Security*: https://www.rfc-editor.org/rfc/rfc9700.html
