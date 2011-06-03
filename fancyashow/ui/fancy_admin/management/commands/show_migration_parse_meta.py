from django.core.management.base import BaseCommand
from fancyashow.db.models        import Show

class Command(BaseCommand):
  def handle(self, **options):      
    migrate = """
    function() {
      db[collection].find(query).forEach(function(show) {
        show.parse_meta.image_url = show.image_url;
        show.parse_meta.resources = show.parsed_resources;
        show.image_url            = null;

        delete show.parsed_resources;
        
        db.show.save(show);
      });
    }
    """

    Show.objects.exec_js(migrate)
    