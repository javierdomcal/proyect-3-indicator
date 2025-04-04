%chk=arcas88augpc4.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(8,8)/gen gfinput fchk=all density=current iop(5/33=1) out=wfx

arcas88augpc4 argon CASSCF(8,8) aug-pc-4

0 1
Ar 0.0 0.0 0.0

Ar     0
S    15   1.00
      0.944510D+07           0.647130D-06
      0.141410D+07           0.503360D-05
      0.321810D+06           0.264820D-04
      0.911580D+05           0.111900D-03
      0.297430D+05           0.407910D-03
      0.107400D+05           0.133090D-02
      0.419000D+04           0.396580D-02
      0.173890D+04           0.108630D-01
      0.759290D+03           0.271590D-01
      0.345500D+03           0.605140D-01
      0.162360D+03           0.113510D+00
      0.788880D+02           0.158270D+00
      0.393210D+02           0.139000D+00
      0.199180D+02           0.556450D-01
      0.957640D+01           0.513770D-02
S    12   1.00
      0.297430D+05          -0.562840D-06
      0.107400D+05          -0.404410D-06
      0.419000D+04          -0.236590D-04
      0.173890D+04          -0.102670D-03
      0.759290D+03          -0.778910D-03
      0.345500D+03          -0.337400D-02
      0.162360D+03          -0.154820D-01
      0.788880D+02          -0.416870D-01
      0.393210D+02          -0.894240D-01
      0.199180D+02          -0.106220D-01
      0.957640D+01           0.200990D+00
      0.491610D+01           0.367220D+00
S    12   1.00
      0.107400D+05          -0.430140D-05
      0.419000D+04          -0.322640D-04
      0.173890D+04          -0.215590D-03
      0.759290D+03          -0.124380D-02
      0.345500D+03          -0.612440D-02
      0.162360D+03          -0.258780D-01
      0.788880D+02          -0.748300D-01
      0.393210D+02          -0.152780D+00
      0.199180D+02          -0.370790D-01
      0.957640D+01           0.435240D+00
      0.491610D+01           0.885820D+00
      0.246480D+01           0.609510D+00
S    1   1.00
      0.118300D+01           0.100000D+01
S    1   1.00
      0.575210D+00           0.100000D+01
S    1   1.00
      0.270410D+00           0.100000D+01
S    1   1.00
      0.123120D+00           0.100000D+01
S    1   1.00
      0.513800D-01           0.100000D+01
P    11   1.00
      0.130060D+05           0.869280D-05
      0.307810D+04           0.776110D-04
      0.999560D+03           0.452490D-03
      0.380970D+03           0.205950D-02
      0.160280D+03           0.758720D-02
      0.744940D+02           0.218220D-01
      0.360650D+02           0.543320D-01
      0.181640D+02           0.104420D+00
      0.946650D+01           0.146450D+00
      0.516300D+01           0.144260D+00
      0.280850D+01           0.943790D-01
P    11   1.00
      0.307810D+04           0.275660D-05
      0.999560D+03          -0.182720D-05
      0.380970D+03           0.453980D-04
      0.160280D+03          -0.255510D-03
      0.744940D+02          -0.549680D-03
      0.360650D+02          -0.835420D-02
      0.181640D+02          -0.165040D-01
      0.946650D+01          -0.765420D-01
      0.516300D+01           0.166060D-02
      0.280850D+01           0.120150D-02
      0.152350D+01           0.851690D+00
P    1   1.00
      0.743790D+00           0.100000D+01
P    1   1.00
      0.356800D+00           0.100000D+01
P    1   1.00
      0.162210D+00           0.100000D+01
P    1   1.00
      0.699560D-01           0.100000D+01
P    1   1.00
      0.277700D-01           0.100000D+01
D    1   1.00
      0.263300D+02           0.100000D+01
D    1   1.00
      0.753000D+01           0.100000D+01
D    1   1.00
      0.260000D+01           0.100000D+01
D    1   1.00
      0.930000D+00           0.100000D+01
D    1   1.00
      0.410000D+00           0.100000D+01
D    1   1.00
      0.170000D+00           0.100000D+01
D    1   1.00
      0.833100D-01           0.100000D+01
F    1   1.00
      0.453000D+01           0.100000D+01
F    1   1.00
      0.106000D+01           0.100000D+01
F    1   1.00
      0.440000D+00           0.100000D+01
F    1   1.00
      0.111100D+00           0.100000D+01
G    1   1.00
      0.218000D+01           0.100000D+01
G    1   1.00
      0.730000D+00           0.100000D+01
G    1   1.00
      0.138900D+00           0.100000D+01
H    1   1.00
      0.112000D+01           0.100000D+01
H    1   1.00
      0.166600D+00           0.100000D+01
 ****

arcas88augpc4.wfx

