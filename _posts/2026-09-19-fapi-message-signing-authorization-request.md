---
layout: post
title: "FAPI 2.0 Message Signing：Authorization Request はどこで署名・検証されるのか"
date: 2026-09-19 04:38:00 +0900
categories: [authorization, oauth, fapi]
---

FAPI 2.0 Message Signing は、FAPI 2.0 Security Profile に基づく特定の request / response を署名・検証するためのプロファイルです。この記事では、そのうち **Authorization Request の署名**だけを扱います。

## この記事について

**記事タイプ:** Flow / Requirement  
**対象読者:** FAPI 2.0 の Client / Authorization Server を実装・レビューする開発者  
**この記事で伝えること:** Client が Authorization Request のパラメータを signed request object に入れて PAR Endpoint へ送り、Authorization Server がどこで何を検証するか  
**扱わないこと:** Authorization Response の JARM、Introspection Response、ID Token、Resource Request / Response、非否認性一般の評価

## 1. Authorization Request signing の位置

FAPI 2.0 Message Signing §5.3 は、pushed authorization request を署名することで NR1 を扱います。また FAPI 2.0 が PAR を使用するため、signed pushed authorization request によって front-channel の Authorization Request に関する NR2 も扱われると説明しています。

ここで重要なのは、署名された request object を Browser 経由で Authorization Endpoint へ直接送る構成ではないことです。Client は signed request object を **PAR Endpoint** へ送ります。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant UA as User Agent
    C->>C: Authorization parameters を JAR に格納して署名
    C->>AS: PAR request + signed request object
    AS->>AS: JAR と追加要件を検証
    AS-->>C: request_uri
    C->>UA: client_id + request_uri
    UA->>AS: Authorization Request
</pre>

## 2. Client はすべての Authorization parameter を signed request object に入れる

FAPI 2.0 Message Signing §5.3.2 は、Authorization Request signing を実装する Client に対し、**すべての Authorization parameter を JAR に従う signed request object に格納し、PAR Endpoint へ送信することを要求しています（shall）**。

JAR は RFC 9101、PAR は RFC 9126 で定義されています。したがって、FAPI 2.0 Message Signing は Authorization Request の署名形式と送信経路を新規に定義するのではなく、JAR と PAR を組み合わせ、その利用方法に追加要件を設定しています。

## 3. `aud` は Authorization Server の issuer identifier URL

§5.3.2 は Client に対し、request object の `aud` claim として Authorization Server の issuer identifier URL を送ることを要求しています（shall）。

Authorization Server 側について §5.3.1 は、`aud` が Authorization Server の issuer identifier URL そのもの、またはその URL を含む配列であることを要求することを shall としています。

<pre class="mermaid">
flowchart TD
    A[Signed request object] --> B[aud を取得]
    B --> C{AS issuer URL か\nそれを含む配列か}
    C -->|Yes| D[次の検証へ]
    C -->|No| E[要件を満たさない]
</pre>

## 4. `nbf` と `exp` の時間条件

Client は §5.3.2 により、request object に `nbf` claim を送ることを要求されています（shall）。また `exp` claim も送信し、その lifetime を60分以内にしなければなりません（shall）。

Authorization Server は §5.3.1 により、`nbf` が現在から60分より前ではないことを要求しなければなりません。さらに `exp` は `nbf` から60分を超えない lifetime であることを要求します。

このため、Authorization Server の確認対象には署名の検証だけでなく、request object の時間条件も含まれます。

## 5. `typ` は Client と Authorization Server で強度が異なる

Client について §5.3.2 は、JOSE Header の `typ` に `oauth-authz-req+jwt` を設定することを **should** としています。

一方、Authorization Server について §5.3.1 は、`typ` が `oauth-authz-req+jwt` である request object を受け入れることを **shall** としています。

Client 側の should と Authorization Server 側の shall は同じ強度ではありません。実装要件を読む際には、この違いを維持する必要があります。

## 6. Authorization Server は PAR Endpoint で JAR を検証する

§5.3.1 は Authorization Server に対し、PAR Endpoint で RFC 9101 に従う signed request object をサポートし、使用を要求し、検証することを shall としています。

処理をまとめると次の順序になります。

1. Client が Authorization parameter を作成する。
2. Client がそれらを JAR request object に格納して署名する。
3. Client が signed request object を PAR Endpoint へ送る。
4. Authorization Server が JAR の署名・内容を検証する。
5. Authorization Server が `aud`、`nbf`、`exp` など FAPI 2.0 Message Signing の追加要件を確認する。
6. PAR が成功すると、以後の Authorization Request は PAR で得た `request_uri` を使って進む。

## 7. Front-channel Authorization Request の扱い

FAPI 2.0 Message Signing §5.3 は、FAPI 2.0 が PAR を使用するため、pushed authorization request が署名されていれば NR2 も達成されると説明しています。

ただし §6.4 は、front-channel Authorization Request そのものには non-repudiation が提供されないことを明記しています。つまり、PAR へ送られた signed request object と、その後 Browser を経由する front-channel message は区別して扱う必要があります。

## 8. 一次資料

- OpenID Foundation: [FAPI 2.0 Message Signing — Final](https://openid.net/specs/fapi-message-signing-2_0-final.html)
- RFC Editor: [RFC 9101 — The OAuth 2.0 Authorization Framework: JWT-Secured Authorization Request (JAR)](https://www.rfc-editor.org/rfc/rfc9101.html)
- RFC Editor: [RFC 9126 — OAuth 2.0 Pushed Authorization Requests](https://www.rfc-editor.org/rfc/rfc9126.html)

参照した主要節: FAPI 2.0 Message Signing §5.3, §5.3.1, §5.3.2, §6.4  
最終確認: 2026-09-19
