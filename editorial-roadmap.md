---
layout: page
title: "Editorial Roadmap"
permalink: /roadmap/
---

今後の記事候補は、仕様名ではなく「誰に何を伝える記事か」が分かる単位で管理します。掲載順は公開予定を意味しません。

| 記事タイプ | 想定テーマ | 対象読者 | 中心となる一次資料 |
|---|---|---|---|
| Feature Deep Dive | DPoP proof はどの HTTP request に何を証明するのか | OAuth Client / Resource Server 実装者 | RFC 9449 |
| Comparison / Requirement | MTLS と DPoP で sender-constrained token の処理がどう異なるか | OAuth / API セキュリティ実装者 | RFC 8705, RFC 9449 |
| Flow | PAR で Authorization Request がどのように2段階化されるか | OAuth Client / Authorization Server 実装者 | RFC 9126 |
| Feature Deep Dive | RAR の `authorization_details` が表現する認可情報 | Authorization Server / Client 実装者 | RFC 9396 |
| Overview | OpenID Connect Core の Authorization Code Flow で ID Token が担う役割 | OIDC 初学者・実装者 | OpenID Connect Core 1.0 |
| Requirement | OIDC ID Token の検証項目と検証順序 | RP 実装者 | OpenID Connect Core 1.0 |
| Flow | FAPI 2.0 Message Signing が request / response のどこに署名を追加するか | FAPI 実装者 | FAPI 2.0 Message Signing |
| Feature Deep Dive | SCIM PATCH の add / remove / replace と path 処理 | SCIM Service Provider 実装者 | RFC 7644 |
| Feature Deep Dive | SCIM Group membership の表現と更新 | SCIM Client / Service Provider 実装者 | RFC 7643, RFC 7644 |
| Feature Deep Dive | WebAuthn Level 3 の related origins が RP ID の利用範囲をどう拡張するか | WebAuthn RP 実装者 | WebAuthn Level 3 |
| Flow | WebAuthn conditional mediation の処理フロー | WebAuthn RP / frontend 実装者 | WebAuthn Level 3 |
| Overview | JWS / JWE / JWK / JWKS の役割と関係 | JOSE を初めて扱う実装者 | RFC 7515–7518 |

新規記事を作る前に、Reader / Question / Answer / Scope / Out of scope / Primary sources / Diagram の Article brief を確定します。

既存記事に新しい論点を追加する場合、その論点が既存記事の中心テーマから外れるなら、追記せず別記事として扱います。
