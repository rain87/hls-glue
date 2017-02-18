#!/usr/bin/perl -w

while(<>)
{
  next unless /^#EXTINF:0\, (.*)$/;
  $name = $1;
  die 'wut' unless <> =~ /play\.lanet\.tv\/live\/(.*)$/;
  $path = $1;
  $path =~ s/\.m3u8/\.ts/;
  print << "SQL_STATEMENT";
INSERT INTO "mt_cds_object" (parent_id,object_type,upnp_class,dc_title,location,resources,mime_type)
VALUES(230,10,"object.item.videoItem","$name","http://kyiv.indolence.name:9090/tv/$path","0~protocolInfo=http-get%3A%2A%3Avideo%2Fx-msvideo%3A%2A~~","video/x-msvideo");
SQL_STATEMENT
}
