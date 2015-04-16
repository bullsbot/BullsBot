class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    def __getattr__(self, attr):
        return self.get(attr)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def get_zoned_dates_for_format_string(fmt_string, date):
    import pytz
    from string import Formatter
    sf = Formatter()
    variables = {}
    for literal_text, field_name, format_spec, conversion in sf.parse(fmt_string):
        if field_name in pytz.common_timezones:
            variables[field_name] = date.astimezone(pytz.timezone(field_name))
    return variables