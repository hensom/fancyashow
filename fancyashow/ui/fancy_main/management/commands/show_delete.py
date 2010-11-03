from fancyashow.ui.fancy_main.management.commands import ShowCommand

class Command(ShowCommand):
  def handle_shows(self, shows, **options):
    shows.delete()