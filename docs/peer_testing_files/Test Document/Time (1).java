// File: Time.java  Author: Alan Kennedy  Date: Jan. 14, 2013
// Description: A class to represent a time on a 24 hour clock. Objects of
//              this class will store an hour (from 0 to 23) and a minute
//              from (0 to 59).

public class Time {
   private int hour, minute;
   public Time(int h, int m) {
      hour=h%24;
      minute=m%60;
   }
   public String toString() {
      String h="", m="";
      if(hour<10) h="0";
      if(minute<10) m="0";
      return h + hour + ":" + m + minute;
  }
}