---
layout: page
title: "Editorial Roadmap"
permalink: /roadmap/
---

今後の記事候補は、仕様名ではなく「誰に何を伝える記事か」が分かる単位で管理します。掲載順は公開予定を意味しません。

## OAuth / API Security

### DPoP proof は何を証明するのか

- **記事タイプ:** Feature Deep Dive
- **対象読者:** OAuth Client / Resource Server 実装者
- **中心となる一次資料:** RFC 9449

### MTLS と DPoP で sender-constrained token の処理はどう異なるか

- **記事タイプ:** Comparison / Requirement
- **対象読者:** OAuth / API セキュリティ実装者
- **中心となる一次資料:** RFC 8705、RFC 9449

### PAR で Authorization Request はどのように2段階化されるか

- **記事タイプ:** Flow
- **対象読者:** OAuth Client / Authorization Server 実装者
- **中心となる一次資料:** RFC 9126

### RAR の `authorization_details` は何を表現するのか

- **記事タイプ:** Feature Deep Dive
- **対象読者:** Authorization Server / Client 実装者
- **中心となる一次資料:** RFC 9396

## OpenID Connect / FAPI

### Authorization Code Flow で ID Token は何を担うのか

- **記事タイプ:** Overview
- **対象読者:** OIDC 初学者・実装者
- **中心となる一次資料:** OpenID Connect Core 1.0

### ID Token はどの項目をどの順序で検証するのか

- **記事タイプ:** Requirement
- **対象読者:** RP 実装者
- **中心となる一次資料:** OpenID Connect Core 1.0

### FAPI 2.0 Message Signing は request / response のどこに署名を追加するのか

- **記事タイプ:** Flow
- **対象読者:** FAPI 実装者
- **中心となる一次資料:** FAPI 2.0 Message Signing

## SCIM

### SCIM PATCH の add / remove / replace と path はどう処理されるか

- **記事タイプ:** Feature Deep Dive
- **対象読者:** SCIM Service Provider 実装者
- **中心となる一次資料:** RFC 7644

### Group membership はどのように表現・更新されるか

- **記事タイプ:** Feature Deep Dive
- **対象読者:** SCIM Client / Service Provider 実装者
- **中心となる一次資料:** RFC 7643、RFC 7644

## WebAuthn

### related origins は RP ID の利用範囲をどう扱うか

- **記事タイプ:** Feature Deep Dive
- **対象読者:** WebAuthn RP 実装者
- **中心となる一次資料:** WebAuthn Level 3

### conditional mediation の処理フロー

- **記事タイプ:** Flow
- **対象読者:** WebAuthn RP / frontend 実装者
- **中心となる一次資料:** WebAuthn Level 3

## JOSE

### JWS / JWE / JWK / JWKS はそれぞれ何を担うのか

- **記事タイプ:** Overview
- **対象読者:** JOSE を初めて扱う実装者
- **中心となる一次資料:** RFC 7515–7518

新規記事を作る前に、Reader / Question / Answer / Scope / Out of scope / Primary sources / Diagram の Article brief を確定します。

既存記事に新しい論点を追加する場合、その論点が既存記事の中心テーマから外れるなら、追記せず別記事として扱います。
