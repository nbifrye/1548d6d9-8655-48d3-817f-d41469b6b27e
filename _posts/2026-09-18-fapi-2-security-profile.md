---
layout: post
title: "FAPI 2.0 Security Profile：OAuth を高保証 API 向けにどう絞り込むか"
date: 2026-09-18 09:20:00 +0900
categories: [authorization, api-security, fapi]
---

FAPI 2.0 Security Profile は、2025年2月22日に OpenID Foundation の **Final Specification** として公開された、高いセキュリティ要求を持つ API 向けの OAuth 2.0 プロファイルです。

金融分野から発展しましたが、適用先は金融 API に限定されません。高価値データを扱う API で、クライアント、Authorization Server、Resource Server 間のセキュリティ特性を相互運用可能に揃えるための仕様です。

## 読み方
FAPI 2.0 は別の認可プロトコルというより、OAuth 2.0 と関連 RFC の選択肢を安全側へ絞るプロファイルです。OAuth Security BCP (RFC 9700) の推奨も前提にします。

焦点になるのは、認可リクエストの保護、authorization code の悪用防止、client authentication、sender-constrained token などです。

## Message Signing
FAPI 2.0 Message Signing は 2025年9月に Final Specification となり、特定の request / response の署名・検証と non-repudiation を扱います。すべての導入で必須という意味ではなく、セキュリティ目標に応じて評価します。

## 参照
- https://openid.net/specs/fapi-security-profile-2_0.html
- https://openid.net/specs/fapi-attacker-model-2_0-final.html
- https://openid.net/specs/fapi-message-signing-2_0.html
- https://www.rfc-editor.org/rfc/rfc9700.html

最終確認: 2026-09-18
