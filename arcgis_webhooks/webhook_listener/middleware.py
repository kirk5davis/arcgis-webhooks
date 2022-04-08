
class DarkModePreferenceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            dark_mode_preference = request.COOKIES["halfmoon_preferredMode"]
        except KeyError:
            dark_mode_preference = 'dark-mode'
            request.COOKIES["halfmoon_preferredMode"] = dark_mode_preference
        request.dark_mode_preference = dark_mode_preference
        response = self.get_response(request)
        return response