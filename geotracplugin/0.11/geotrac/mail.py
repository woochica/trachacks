from geotrac.ticket import GeoTrac

try:
    from mail2trac.email2trac import EmailException
    from mail2trac.email2ticket import EmailToTicket

    class GeoMailToTicket(EmailToTicket):
        """create a ticket from an email with a location"""
        

        def fields(self, message, **fields):

            # if you don't have GeoTrac enabled, why are you using this plugin?
            assert GeoTrac in self.env.components 
            geotrac = self.env.components[GeoTrac]

            subject = message['subject']
            location = ''
            if '@' in subject:
                subject, location = [i.strip() for i in subject.split('@', 1)]
                message['subject'] = subject
                fields['location'] = location
            else:
                if geotrac.mandatory_location:
                    raise EmailException('Location required. Please email with "%s @ <location>" in your subject.' % subject)

            return EmailToTicket.fields(self, message, **fields)


except ImportError:
    pass
