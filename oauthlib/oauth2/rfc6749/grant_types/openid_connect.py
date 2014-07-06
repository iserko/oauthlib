# -*- coding: utf-8 -*-
"""
oauthlib.oauth2.rfc6749.grant_types.openid_connect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import unicode_literals, absolute_import

from json import loads

from .base import GrantTypeBase
from .authorization_code import AuthorizationCodeGrant
from .implicit import ImplicitGrant
from ..errors import InvalidRequestError, LoginRequired, ConsentRequired
from ..request_validator import RequestValidator


class OpenIDConnectBase(GrantTypeBase):

    def add_id_token(self, token, request):
        # Treat it as normal OAuth 2 auth code request if openid is not present
        if not 'openid' in request.scopes:
            return token

        # TODO: if max_age, then we must include auth_time here
        # TODO: acr claims

    def openid_authorization_validator(self, request):
        """Perform OpenID Connect specific authorization request validation.

        display
                OPTIONAL. ASCII string value that specifies how the
                Authorization Server displays the authentication and consent
                user interface pages to the End-User. The defined values are:

                    page - The Authorization Server SHOULD display the
                    authentication and consent UI consistent with a full User
                    Agent page view. If the display parameter is not specified,
                    this is the default display mode.

                    popup - The Authorization Server SHOULD display the
                    authentication and consent UI consistent with a popup User
                    Agent window. The popup User Agent window should be of an
                    appropriate size for a login-focused dialog and should not
                    obscure the entire window that it is popping up over.

                    touch - The Authorization Server SHOULD display the
                    authentication and consent UI consistent with a device that
                    leverages a touch interface.

                    wap - The Authorization Server SHOULD display the
                    authentication and consent UI consistent with a "feature
                    phone" type display.

                The Authorization Server MAY also attempt to detect the
                capabilities of the User Agent and present an appropriate
                display.

        prompt
                OPTIONAL. Space delimited, case sensitive list of ASCII string
                values that specifies whether the Authorization Server prompts
                the End-User for reauthentication and consent. The defined
                values are:

                    none - The Authorization Server MUST NOT display any
                    authentication or consent user interface pages. An error is
                    returned if an End-User is not already authenticated or the
                    Client does not have pre-configured consent for the
                    requested Claims or does not fulfill other conditions for
                    processing the request. The error code will typically be
                    login_required, interaction_required, or another code
                    defined in Section 3.1.2.6. This can be used as a method to
                    check for existing authentication and/or consent.

                    login - The Authorization Server SHOULD prompt the End-User
                    for reauthentication. If it cannot reauthenticate the
                    End-User, it MUST return an error, typically
                    login_required.

                    consent - The Authorization Server SHOULD prompt the
                    End-User for consent before returning information to the
                    Client. If it cannot obtain consent, it MUST return an
                    error, typically consent_required.

                    select_account - The Authorization Server SHOULD prompt the
                    End-User to select a user account. This enables an End-User
                    who has multiple accounts at the Authorization Server to
                    select amongst the multiple accounts that they might have
                    current sessions for. If it cannot obtain an account
                    selection choice made by the End-User, it MUST return an
                    error, typically account_selection_required.

                The prompt parameter can be used by the Client to make sure
                that the End-User is still present for the current session or
                to bring attention to the request. If this parameter contains
                none with any other value, an error is returned.

        max_age
                OPTIONAL. Maximum Authentication Age. Specifies the allowable
                elapsed time in seconds since the last time the End-User was
                actively authenticated by the OP. If the elapsed time is
                greater than this value, the OP MUST attempt to actively
                re-authenticate the End-User. (The max_age request parameter
                corresponds to the OpenID 2.0 PAPE [OpenID.PAPE] max_auth_age
                request parameter.) When max_age is used, the ID Token returned
                MUST include an auth_time Claim Value.

        ui_locales
                OPTIONAL. End-User's preferred languages and scripts for the
                user interface, represented as a space-separated list of BCP47
                [RFC5646] language tag values, ordered by preference. For
                instance, the value "fr-CA fr en" represents a preference for
                French as spoken in Canada, then French (without a region
                designation), followed by English (without a region
                designation). An error SHOULD NOT result if some or all of the
                requested locales are not supported by the OpenID Provider.

        id_token_hint
                OPTIONAL. ID Token previously issued by the Authorization
                Server being passed as a hint about the End-User's current or
                past authenticated session with the Client. If the End-User
                identified by the ID Token is logged in or is logged in by the
                request, then the Authorization Server returns a positive
                response; otherwise, it SHOULD return an error, such as
                login_required. When possible, an id_token_hint SHOULD be
                present when prompt=none is used and an invalid_request error
                MAY be returned if it is not; however, the server SHOULD
                respond successfully when possible, even if it is not present.
                The Authorization Server need not be listed as an audience of
                the ID Token when it is used as an id_token_hint value. If the
                ID Token received by the RP from the OP is encrypted, to use it
                as an id_token_hint, the Client MUST decrypt the signed ID
                Token contained within the encrypted ID Token. The Client MAY
                re-encrypt the signed ID token to the Authentication Server
                using a key that enables the server to decrypt the ID Token,
                and use the re-encrypted ID token as the id_token_hint value.

        login_hint
                OPTIONAL. Hint to the Authorization Server about the login
                identifier the End-User might use to log in (if necessary).
                This hint can be used by an RP if it first asks the End-User
                for their e-mail address (or other identifier) and then wants
                to pass that value as a hint to the discovered authorization
                service. It is RECOMMENDED that the hint value match the value
                used for discovery. This value MAY also be a phone number in
                the format specified for the phone_number Claim. The use of
                this parameter is left to the OP's discretion.

        acr_values
                OPTIONAL. Requested Authentication Context Class Reference
                values. Space-separated string that specifies the acr values
                that the Authorization Server is being requested to use for
                processing this Authentication Request, with the values
                appearing in order of preference. The Authentication Context
                Class satisfied by the authentication performed is returned as
                the acr Claim Value, as specified in Section 2. The acr Claim
                is requested as a Voluntary Claim by this parameter.
        """

        # Treat it as normal OAuth 2 auth code request if openid is not present
        if not 'openid' in request.scopes:
            return

        if request.prompt == 'none' and not request.id_token_hint:
            msg = "Prompt is set to none yet id_token_hint is missing."
            raise InvalidRequestError(request=request, description=msg)

        if request.prompt == 'none':
            if not self.request_validator.validate_silent_login(request):
                raise LoginRequired(request=request)
            if not self.request_validator.validate_silent_authorization(request):
                raise ConsentRequired(request=request)

        request.claims = loads(request.claims) if request.claims else {}

        if not self.request_validator.validate_user_match(
            request.id_token_hint, request.scopes, request.claims, request):
            msg = "Session user does not match client supplied user."
            raise LoginRequired(request=request, description=msg)

        request_info = {
            'display': request.display,
            'prompt': request.prompt.split() if request.prompt else [],
            'ui_locales': request.ui_locales.split() if request.ui_locales else [],
            'id_token_hint': request.id_token_hint,
            'login_hint': request.login_hint,
        }

        return request_info


class OpenIDConnectAuthCode(OpenIDConnectBase):

    def __init__(self, request_validator=None):
        self.request_validator = request_validator or RequestValidator()
        self.auth_code = AuthorizationCodeGrant(
            request_validator=request_validator)
        self.auth_code.register_authorization_validator(
            self.openid_authorization_validator)
        self.auth_code.register_token_modifier(self.add_id_token)

    def create_authorization_response(self, request, token_handler):
        return self.auth_code.create_authorization_response(
            request, token_handler)

    def create_token_response(self, request, token_handler):
        return self.auth_code.create_token_response(request, token_handler)

    def validate_authorization_request(self, request):
        """Validates the OpenID Connect authorization request parameters.

        :returns: (list of scopes, dict of request info)

        Note: If request_info['prompt'] is 'none' then no login/authorization
        form should be presented to the user. Instead, a silent
        login/authorization should be performed, e.g. by calling
        create_authorization_response directly.
        """
        return self.auth_code.validate_authorization_request(request)

    # TODO: finish current and not yet existing methods


class OpenIDConnectImplicit(OpenIDConnectBase):

    def __init__(self, request_validator=None):
        self.request_validator = request_validator or RequestValidator()
        self.implicit = ImplicitGrant(
            request_validator=request_validator)
        self.implicit.register_response_type('id_token')
        self.implicit.register_response_type('id_token token')
        self.implicit.register_authorization_validator(
            self.openid_authorization_validator)
        self.implicit.register_authorization_validator(
            self.openid_implicit_authorization_validator)
        self.implicit.register_token_modifier(self.create_id_token)


    def openid_implicit_authorization_validator(self, request):
        # Undefined in OpenID Connect, fall back to OAuth2 definition.
        if request.response_type == 'token':
            return

    # TODO: the other methods


class OpenIDConnectHybrid(OpenIDConnectBase):

    def __init__(self, request_validator=None):
        self.request_validator = request_validator or RequestValidator()

        self.auth_code = AuthorizationCodeGrant(
            request_validator=request_validator)
        self.auth_code.register_response_type('code id_token')
        self.auth_code.register_response_type('code token')
        self.auth_code.register_response_type('code id_token token')
        self.auth_code.register_authorization_validator(
            self.openid_authorization_validator)
        self.auth_code.register_token_modifier(self.add_id_token)

        self.implicit = ImplicitGrant(
            request_validator=request_validator)
        self.implicit.register_response_type('id_token')
        self.implicit.register_response_type('id_token token')
        self.implicit.register_authorization_validator(
            self.openid_authorization_validator)
        self.implicit.register_authorization_validator(
            self.openid_implicit_authorization_validator)
        self.implicit.register_token_modifier(self.create_id_token)

    # TODO: find out what gotchas there is to hybrid version
    # that sets it apart from merging the two others...

    # TODO: the other methods