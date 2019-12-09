#!/usr/bin/local/perl -w

open(my $fh, '<', "$file_path") or return 0;
    while (my $line = <$fh>) {
        chomp($line);
        my ($key,$group,$value,$version,$file,$count) = split(/,/,$line);
    my $key = 1;
    foreach my $k (@{$aref}) {
        if ($k->{"group"} eq $group) {
        $k->{"values"} = [ sort uniq $value, @{$k->{"values"}} ];
        $key = 0;
        }
    }
        push @{ $aref }, {
            group => $group,
            values => [ $value ]
        } if ($key);
    }
    close ($fh);
