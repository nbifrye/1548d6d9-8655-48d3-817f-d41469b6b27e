---
layout: page
title: "Editorial Roadmap"
permalink: /roadmap/
---

今後の記事候補は、仕様名ではなく「誰に何を伝える記事か」が分かる単位で管理します。掲載順は公開予定を意味しません。公開済みテーマは候補へ戻さず、同じ Reader / Question / Scope の記事を再作成しません。

## OAuth / API Security

### DPoP proof は何を証明するのか

- **記事タイプ:** Feature Deep Dive
- **対象読者:** OAuth Client / Resource Server 実装者
- **中心となる一次資料:** RFC 9449

### MTLS と DPoP で sender-constrained token の処理はどう異なるか

- **記事タイプ:** Comparison / Requirement
- **対象読者:** OAuth / API セキュリティ実装者
- **中心となる一次資料:** RFC 8705、RFC 9449

### RAR の `authorization_details` は何を表現するのか

- **記事タイプ:** Feature Deep Dive
- **対象読者:** Authorization Server / Client 実装者
- **中心となる一次資料:** RFC 9396

## OpenID Connect / FAPI

### Authorization Code Flow で ID Token は何を担うのか

- **記事タイプ:** Overview
- **対象読者:** OIDC 初学者・実装者
- **中心となる一次資料:** OpenID Connect Core 1.0

### FAPI 2.0 Message Signing は request / response のどこに署名を追加するのか

- **記事タイプ:** Flow
- **対象読者:** FAPI 実装者
- **中心となる一次資料:** FAPI 2.0 Message Signing

## SCIM

## WebAuthn

## JOSE

### JWS / JWE / JWK / JWKS はそれぞれ何を担うのか

- **記事タイプ:** Overview
- **対象読者:** JOSE を初めて扱う実装者
- **中心となる一次資料:** RFC 7515–7518

新規記事を作る前に、Reader / Question / Answer / Scope / Out of scope / Primary sources / Diagram の Article brief を確定します。

既存記事に新しい論点を追加する場合、その論点が既存記事の中心テーマから外れるなら、追記せず別記事として扱います。

## Published-topic registry

以下は公開済みの canonical topic です。同じ Reader / Question / Scope で新規記事を作成せず、追加事項は原則として canonical article を更新します。

- PAR の2段階 Authorization Request → `2026-09-19-oauth-pushed-authorization-requests.md`
- Authorization Code Flow の ID Token validation → `2026-09-19-oidc-id-token-validation.md`
- SCIM PATCH の add / remove / replace / path → `2026-09-19-scim-patch-add-remove-replace.md`
- SCIM Group membership の表現・更新 → `2026-09-19-scim-group-membership.md`
- WebAuthn conditional mediation authentication → `2026-09-19-webauthn-conditional-mediation-authentication.md`
- WebAuthn Related Origin Requests → `2026-09-19-webauthn-related-origin-requests.md`

候補追加時には、この registry と `_posts/` 全体の両方を確認します。registry は検索の代替ではなく、見落としを減らす補助索引です。
