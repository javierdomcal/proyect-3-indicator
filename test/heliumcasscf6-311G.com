%chk=heliumcasscf6-311G.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/6-311G gfinput fchk=all density=current iop(5/33=1) out=wfx

heliumcasscf6-311G helium CASSCF(2,2) 6-311G

0 1
He    0.0000   0.0000   0.0000

heliumcasscf6-311G.wfx

