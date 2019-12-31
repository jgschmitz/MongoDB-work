#!/usr/bin/perl -w;

use strict;
use Exporter;
use vars qw($VERSION @ISA @EXPORT @EXPORT_OK %EXPORT_TAGS);
use MongoDB;


$VERSION     = 2.00;
@ISA         = qw(Exporter);
@EXPORT      = qw();
@EXPORT_OK   = qw();
%EXPORT_TAGS = ( DEFAULT => [qw()],
                 Both    => [qw()]);

sub new {
    my ($class, $args) = @_;
    my $self = {
        host     => $args->{host} || 'localhost',       
        port     => $args->{port} || '27017',
        database => $args->{database} || '',
        connection => $class->_set_connection(),
    };
    return bless $self, $class;
}

sub _set_connection {
    my $self = shift;
    my $client = MongoDB->connect('mongodb://darkstar');
    return $client;
}

sub get_database_names {
    # Lists all databases on the mongo server system call
    my $self = shift;
    return  $self->{connection}->database_names;
}

sub get_database {
    # Returns a MongoDB::Database instance for database with the given $name
    my ($self, $dbname) = @_;
    return $self->{connection}->get_database($dbname);
}

sub authenticate {
    my ($self, $args) = @_;
    $self = {
        dbname => $args->{dbname},
        user => $args->{user},
        password => $args->{password}
    };
    $self->{connection}->authenticate($self->{dbname}, $self->{user}, $self->{password});
}
1;
