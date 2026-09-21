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

### OAuth / API Security

- OAuth 2.0 Security Best Current Practice（RFC 9700）の主要な更新・セキュリティ要件 → `2026-09-18-oauth-security-bcp-rfc9700.md`
- DPoP proof と HTTP request の binding / validation → `2026-09-19-dpop-proof-http-request.md`
- DPoP server-provided nonce の challenge / retry 処理 → `2026-09-19-dpop-server-provided-nonce.md`
- Authorization Server Metadata の metadata document と主要 member → `2026-09-19-oauth-authorization-server-metadata.md`
- Device Authorization Grant の device authorization / polling flow → `2026-09-19-oauth-device-authorization-grant.md`
- Dynamic Client Registration の registration request / response → `2026-09-19-oauth-dynamic-client-registration.md`
- Dynamic Client Registration Management の read / update / delete → `2026-09-20-oauth-dynamic-client-registration-management.md`
- JWT を用いる OAuth client authentication → `2026-09-19-oauth-jwt-client-authentication.md`
- mTLS client authentication → `2026-09-19-oauth-mtls-client-authentication.md`
- PKCE の code_verifier / code_challenge → `2026-09-19-oauth-pkce-code-verifier-challenge.md`
- PAR の2段階 Authorization Request → `2026-09-19-oauth-pushed-authorization-requests.md`
- Resource Indicators の `resource` parameter → `2026-09-19-oauth-resource-indicators.md`
- OAuth Token Exchange の token exchange request / response → `2026-09-19-oauth-token-exchange.md`
- Token Introspection の `active` と introspection response → `2026-09-19-oauth-token-introspection-active.md`
- Token Revocation の revocation request / response → `2026-09-19-oauth-token-revocation.md`
- RAR の `authorization_details` の構造と処理 → `2026-09-19-rar-authorization-details.md`
- JAR の Request Object と Authorization Request → `2026-09-20-oauth-jar-request-object.md`
- JWT Profile for OAuth Access Tokens の Access Token validation → `2026-09-20-oauth-jwt-access-token-validation.md`
- mTLS certificate-bound Access Token の binding / validation → `2026-09-20-oauth-mtls-certificate-bound-access-token.md`
- mTLS と DPoP の sender-constrained Access Token の binding / validation → `2026-09-20-oauth-mtls-dpop-sender-constraint.md`
- Protected Resource Metadata の metadata document と discovery → `2026-09-20-oauth-protected-resource-metadata.md`
- Authorization Response の `iss` と expected issuer の validation → `2026-09-20-oauth-authorization-response-issuer.md`
- Browser-Based Application の BFF / token-mediating backend / browser-based OAuth client の architecture pattern → `2026-09-20-oauth-browser-application-architecture-patterns.md`
- Client Credentials Grant の confidential client authentication / Token Request / Access Token Response → `2026-09-21-oauth-client-credentials-grant.md`
- Refresh Token による Access Token 更新の request / validation / response → `2026-09-21-oauth-refresh-token-request.md`
- Authorization Code Grant の Authorization Endpoint request / response → `2026-09-21-oauth-authorization-code-authorization-endpoint.md`
- Authorization Code の Token Endpoint exchange / validation / response → `2026-09-21-oauth-authorization-code-token-exchange.md`
- Token Endpoint の error response / standard error code / `invalid_client` の HTTP status 処理 → `2026-09-21-oauth-token-endpoint-error-response.md`
- Bearer Access Token の Protected Resource request / token placement / `WWW-Authenticate` error response → `2026-09-21-oauth-bearer-protected-resource-request.md`
- Token Endpoint の successful response / JSON member / scope / cache 制御 → `2026-09-21-oauth-token-endpoint-successful-response.md`
- OAuth Client Type の confidential / public の判定基準と client authentication との関係 → `2026-09-22-oauth-client-types.md`
- OAuth Access Token scope の構文 / requested scope と issued scope の関係 → `2026-09-22-oauth-access-token-scope.md`
- Resource Owner Password Credentials Grant の request 構造と RFC 9700 の利用禁止要件 → `2026-09-22-oauth-resource-owner-password-credentials.md`
- Client password authentication の HTTP Basic / request body credential 配置と要件 → `2026-09-22-oauth-client-password-authentication.md`
- Implicit Grant の `response_type=token` / fragment response と RFC 9700 の `SHOULD NOT` → `2026-09-22-oauth-implicit-grant.md`
- OAuth `redirect_uri` の登録 / validation / exact string matching → `2026-09-22-oauth-redirect-uri-validation.md`
- OAuth `state` parameter の request / response と CSRF protection の要件 → `2026-09-22-oauth-state-csrf-protection.md`

### OpenID Connect / FAPI

- FAPI 2.0 Security Profile の全体像と主要構成 → `2026-09-18-fapi-2-security-profile.md`
- FAPI 2.0 Message Signing の Authorization Request → `2026-09-19-fapi-message-signing-authorization-request.md`
- Authorization Code Flow の ID Token validation → `2026-09-19-oidc-id-token-validation.md`
- Authorization Code Flow における ID Token の役割 → `2026-09-20-oidc-authorization-code-flow-id-token-role.md`
- UserInfo Endpoint の request / response と `sub` validation → `2026-09-20-oidc-userinfo-endpoint.md`
- OpenID Provider Configuration の取得と `issuer` validation → `2026-09-20-oidc-provider-configuration-discovery.md`

### SCIM

- SCIM 2.0 の core concepts / resource model → `2026-09-18-scim-core-concepts.md`
- SCIM filter expression の構文と評価 → `2026-09-19-scim-filter-expressions.md`
- SCIM Group membership の表現・更新 → `2026-09-19-scim-group-membership.md`
- SCIM PATCH の add / remove / replace / path → `2026-09-19-scim-patch-add-remove-replace.md`
- SCIM Bulk Operations の BulkRequest / BulkResponse と `bulkId` → `2026-09-21-scim-bulk-operations.md`
- SCIM sorting の `sortBy` / `sortOrder` と属性値の評価 → `2026-09-21-scim-sorting.md`
- SCIM index-based pagination の `startIndex` / `count` と ListResponse → `2026-09-21-scim-index-based-pagination.md`
- SCIM cursor-based pagination の `cursor` / `nextCursor` と後続ページ取得 → `2026-09-21-scim-cursor-based-pagination.md`
- SCIM Service Provider Configuration の capability discovery → `2026-09-21-scim-service-provider-configuration.md`
- SCIM ResourceTypes の resource type / endpoint / schema discovery → `2026-09-21-scim-resource-types-discovery.md`
- SCIM Schemas の schema / attribute definition discovery → `2026-09-21-scim-schema-discovery.md`
- SCIM Enterprise User extension の組織属性と `manager` representation → `2026-09-21-scim-enterprise-user-extension.md`
- SCIM User.password の writeOnly / returned=never と設定・変更時の処理 → `2026-09-21-scim-password-writeonly.md`
- SCIM authentication / authorization の仕様境界と access control requirement → `2026-09-21-scim-authentication-authorization.md`
- SCIM resource versioning の ETag / `meta.version` と条件付き request → `2026-09-21-scim-resource-versioning-etag.md`
- SCIM partial resource representation の `attributes` / `excludedAttributes` と `returned` characteristic → `2026-09-21-scim-partial-resource-representation.md`
- SCIM resource deletion の DELETE response と削除後の observable behavior → `2026-09-21-scim-delete-resource.md`
- SCIM PUT resource replacement の attribute mutability / required と replacement semantics → `2026-09-21-scim-put-resource-replacement.md`
- SCIM POST resource creation の attribute processing / 201 Created / resource location → `2026-09-21-scim-post-resource-creation.md`
- SCIM Error response の HTTP status / `status` / `scimType` / `detail` 構造 → `2026-09-22-scim-error-response.md`

### WebAuthn

- WebAuthn Level 3 Recommendation の全体像 → `2026-09-18-webauthn-level-3-recommendation.md`
- WebAuthn conditional mediation authentication → `2026-09-19-webauthn-conditional-mediation-authentication.md`
- WebAuthn Related Origin Requests → `2026-09-19-webauthn-related-origin-requests.md`

### JOSE

- JWS / JWE / JWK / JWKS の役割 → `2026-09-20-jose-jws-jwe-jwk-jwks-overview.md`

候補追加時には、この registry と `_posts/` 全体の両方を確認します。registry は検索の代替ではなく、見落としを減らす補助索引です。新規記事を公開した場合は、同じ変更でこの registry に canonical topic を追加します。