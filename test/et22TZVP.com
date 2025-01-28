%chk=et22TZVP.chk
%mem=4GB
%NProcShared=1
#P Opt CASSCF(2,2)/TZVP gfinput fchk=all density=current iop(5/33=1) out=wfx

et22TZVP ethene CASSCF(2,2) TZVP

0 1
C 	0.000	0.000	0.000
C 	0.000	0.000	1.330
H 	0.000	0.920	-0.510
H	0.000	-0.920	-0.510
H	0.000	0.920	1.840
H	0.000	-0.920	1.840

et22TZVP.wfx

