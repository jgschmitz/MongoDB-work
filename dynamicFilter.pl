#!/usr/bin/perl -w
use; strict
my @serchstra;
my $ccount=0;
for(my $id=0;$id < keys %hfields;$id++){
    info("compose search $id ",query_parameters->get("columns[$id][searchable]"),' >',query_parameters->get("columns[$id][search][value]"),'< ',query_parameters->get("columns[$id][data]"));
    if(query_parameters->get("columns[$id][searchable]") eq 'true' &&
        defined query_parameters->get("columns[$id][search][value]") &&
        query_parameters->get("columns[$id][search][value]") ne '')
    {
        my $kvalue=query_parameters->get("columns[$id][search][value]");
        push @serchstra,{ query_parameters->get("columns[$id][data]")  => qr/$kvalue/i};
        $ccount++;
    }
}
push @{$serchstr{q{$and}}},@serchstra;
info("HH0 serchstr is:".Dumper(%serchstr) ."\n---- lengh of serchstra is: " .scalar @serchstra . " but ccount $ccount");
$serchstr = \%serchstr if($ccount > 0);
@ret = $collection->find($serchstr)->fields(\%hfields)->limit(params->{length})->skip(params->{start})->all;
}
