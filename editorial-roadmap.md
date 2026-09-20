---
layout: page
title: "Editorial Roadmap"
permalink: /roadmap/
---

今後の記事候補は、仕様名ではなく「誰に何を伝える記事か」が分かる単位で管理します。掲載順は公開予定を意味しません。公開済みテーマは候補へ戻さず、同じ Reader / Question / Scope の記事を再作成しません。

## OAuth / API Security

## OpenID Connect / FAPI

## SCIM

## WebAuthn

## JOSE

新規記事を作る前に、Reader / Question / Answer / Scope / Out of scope / Primary sources / Diagram の Article brief を確定します。

既存記事に新しい論点を追加する場合、その論点が既存記事の中心テーマから外れるなら、追記せず別記事として扱います。

## Published-topic registry

以下は公開済みの canonical topic です。同じ Reader / Question / Scope で新規記事を作成せず、追加事項は原則として canonical article を更新します。

- DPoP proof と HTTP request の binding / validation → `2026-09-19-dpop-proof-http-request.md`
- mTLS と DPoP の sender-constrained Access Token の binding / validation → `2026-09-20-oauth-mtls-dpop-sender-constraint.md`
- RAR の `authorization_details` の構造と処理 → `2026-09-19-rar-authorization-details.md`
- Authorization Code Flow における ID Token の役割 → `2026-09-20-oidc-authorization-code-flow-id-token-role.md`
- Authorization Code Flow の ID Token validation → `2026-09-19-oidc-id-token-validation.md`
- FAPI 2.0 Message Signing の Authorization Request → `2026-09-19-fapi-message-signing-authorization-request.md`
- PAR の2段階 Authorization Request → `2026-09-19-oauth-pushed-authorization-requests.md`
- SCIM PATCH の add / remove / replace / path → `2026-09-19-scim-patch-add-remove-replace.md`
- SCIM Group membership の表現・更新 → `2026-09-19-scim-group-membership.md`
- WebAuthn conditional mediation authentication → `2026-09-19-webauthn-conditional-mediation-authentication.md`
- WebAuthn Related Origin Requests → `2026-09-19-webauthn-related-origin-requests.md`
- JWS / JWE / JWK / JWKS の役割 → `2026-09-20-jose-jws-jwe-jwk-jwks-overview.md`

候補追加時には、この registry と `_posts/` 全体の両方を確認します。registry は検索の代替ではなく、見落としを減らす補助索引です。
